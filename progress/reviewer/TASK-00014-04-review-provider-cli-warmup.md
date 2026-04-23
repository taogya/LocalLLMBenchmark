# TASK-00014-04 provider status / model pull / model warmup 最終確認

- Status: done
- Role: reviewer
- Parent: TASK-00014
- Related IDs: REQ-00001, FUN-00408, FUN-00409, FUN-00410, CLI-00112, CLI-00113, CLI-00114, CLI-00205, CLI-00309, NFR-00001, NFR-00302, PROG-00103
- 起票日: 2026-04-24

## 目的

TASK-00014 の設計・実装・README 更新を横断で確認し、`provider status` / `model pull` / `model warmup` が初回ベンチ前の導線を補強しつつ既存 CLI を壊していないことを検証する。あわせて、warmup 有無による初回ロード差分を実機で確認する。

## 完了条件

- 着手時点で TASK-00014-01 / 02 / 03 / 05 が `review-pending` または `done` になっている。
- public surface、責務境界、進捗表示、終了コード、README 記述が相互に整合している。
- 標準ライブラリ制約と既存 CLI 非破壊が確認されている。
- Ollama 実機が利用可能な環境で、warmup 実施前後の初回ロード差分または warmup 完了による状態改善が確認され、結果が進捗ログに残っている。
- 必要な検証結果が親 task に引き継げる形で整理されている。

## スコープ外

- 追加実装そのもの
- README / docs の新規執筆

## 進捗ログ

- 2026-04-24 project-master: 起票。設計・実装・README 更新がそろった時点で最終確認を依頼予定。
- 2026-04-24 project-master: ユーザー確認により、warmup 効果の実機確認を任意ではなく本 task の確認観点に含めることを共有。
- 2026-04-24 reviewer: TASK-00014-01 / 05 が done、TASK-00014-02 / 03 が review-pending であることを確認し、README、docs/requirements、docs/design、src、tests を横断確認した。`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK、`PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_providers` は 46 tests OK、`PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_compare_integration tests.test_smoke_checklist` は 13 tests OK。実 CLI では `provider status --config-dir configs` が exit 9、`model pull --config-dir configs --provider ollama --model-ref qwen2:1.5b` と `model warmup --config-dir configs --provider ollama --model-ref qwen2:1.5b` がいずれも exit 4 で、stdout / stderr 分離と negative path の挙動を確認した。一方で `command -v ollama && ollama list` は Ollama CLI は存在するがサーバー未起動で接続できず、warmup 効果の実機確認を完了できなかったため、本 task は `review-pending` を継続する。
- 2026-04-24 reviewer: live Ollama を再確認。`ollama serve` を起動したうえで `ollama list` と `ollama ps` を実行し、`qwen2.5:7b` が inventory に存在し、warmup 前は loaded model がないことを確認した。続けて `PYTHONPATH=src python -m local_llm_benchmark.cli.main provider status --config-dir configs --provider ollama` は reachable / version 0.20.7 / inventory 1 件で exit 0、`model pull --config-dir configs --provider ollama --model-ref qwen2.5:7b` は `already_present` で exit 0、`model warmup --config-dir configs --provider ollama --model-ref qwen2.5:7b` は `ready` / elapsed 12.06s で exit 0 となった。warmup 後の `ollama ps` では `qwen2.5:7b` が loaded 状態になり、warmup 完了による状態改善を確認できた。一方で README の既知制約節には `ollama pull` / `ollama serve` をユーザー側で実施と残っており、`model pull` を提供する現行 public surface と齟齬があるため、本 task は `review-pending` を継続する。
- 2026-04-24 reviewer: docs-writer の差し戻し対応を focused recheck し、[README.md](README.md) と [progress/docs-writer/TASK-00014-03-readme-provider-cli-warmup-update.md](progress/docs-writer/TASK-00014-03-readme-provider-cli-warmup-update.md) を確認した。README の「使い方の概観」「前提環境」「最短手順」「サブコマンド一覧」「既知の制約」は、provider 起動は前提、model 取得は `model pull` または provider CLI の明示操作、暗黙 pull はしないという利用者向け説明で整合しており、前回 blocker だった user-facing 文言の自己矛盾は解消した。`MMDC_REQUIRED=1 bash scripts/verify.sh` を再実行して 10/10 OK を確認し、前回実施済みの focused tests / live smoke は引き続き有効と判断できるため、本 task を `done` に更新した。

## レビュー記録 (reviewer 用)

### 判定

- done (前回 blocker 解消)

### verify.sh 実行結果サマリ

- OK: check_id_format.py
- OK: check_id_uniqueness.py
- OK: check_id_references.py
- OK: check_doc_links.py
- OK: check_progress_format.py
- OK: check_mermaid_syntax.py
- OK: check_markdown_syntax.py
- OK: check_no_implementation_leak.py
- OK: check_role_boundary.py
- OK: check_oos_no_implementation.py

### テスト / コマンド結果サマリ

- OK: `MMDC_REQUIRED=1 bash scripts/verify.sh` を再実行し 10/10 OK
- OK: `PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_providers` (46 tests)
- OK: `PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_compare_integration tests.test_smoke_checklist` (13 tests)
- OK: negative smoke として `PYTHONPATH=src python -m local_llm_benchmark.cli.main provider status --config-dir configs` → exit 9 (CLI-00309), stdout は `providers` / `summary` の 2 セクション JSON、stderr は `[provider status] ... unreachable` の 1 行
- OK: negative smoke として `PYTHONPATH=src python -m local_llm_benchmark.cli.main model pull --config-dir configs --provider ollama --model-ref qwen2:1.5b` → exit 4 (CLI-00304), stderr に開始 / 完了のみ、stdout に `target` / `pull` / `summary`
- OK: negative smoke として `PYTHONPATH=src python -m local_llm_benchmark.cli.main model warmup --config-dir configs --provider ollama --model-ref qwen2:1.5b` → exit 4 (CLI-00304), stderr に開始 / 完了のみ、stdout に `target` / `warmup` / `summary`
- OK: `command -v ollama` → `/opt/homebrew/bin/ollama`
- OK: `ollama serve` → `127.0.0.1:11434` で version 0.20.7 のサーバーを起動
- OK: `ollama list` → `qwen2.5:7b` が inventory に存在
- OK: warmup 前 `ollama ps` → loaded model なし
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main provider status --config-dir configs --provider ollama` → exit 0、reachable / version 0.20.7 / inventory `qwen2.5:7b`
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main model pull --config-dir configs --provider ollama --model-ref qwen2.5:7b` → exit 0、state=`already_present`、next_action=`model_warmup`
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main model warmup --config-dir configs --provider ollama --model-ref qwen2.5:7b` → exit 0、state=`ready`、elapsed=`12.06069591600135`
- OK: warmup 後 `ollama ps` → `qwen2.5:7b` が loaded 状態 (`UNTIL` 約 4 分)

### 確認対象

- progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md
- progress/reviewer/TASK-00014-05-review-provider-cli-warmup-design.md
- progress/programmer/TASK-00014-02-implement-provider-cli-warmup.md
- progress/docs-writer/TASK-00014-03-readme-provider-cli-warmup-update.md
- progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md
- README.md
- docs/requirements/02-functional.md
- docs/requirements/04-out-of-scope.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- docs/development/environment.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/provider_preparation.py
- src/local_llm_benchmark/providers/base.py
- src/local_llm_benchmark/providers/ollama.py
- tests/test_cli_phase3.py
- tests/test_providers.py
- tests/test_run_integration.py
- tests/test_compare_integration.py
- tests/test_smoke_checklist.py

### 発見事項

- 解消: README の user-facing 文言は「`provider status` -> `model pull` -> `model warmup`」という主導線と整合した。[README.md](README.md) では、使い方の概観に「比較したい候補モデルを provider 上に用意する (`model pull` または provider CLI で明示取得)」、前提環境に「Ollama は起動済み」「対象モデルは provider CLI で事前 pull 済みでも後述の `model pull` で明示取得してもよい」、既知の制約に「provider 起動はユーザー側、model 取得は `model pull` または provider CLI の明示操作、暗黙 pull はしない」とあり、前回 blocker だった public surface の自己矛盾は解消している。
- 合格: live Ollama smoke は完了した。`ollama serve` 起動後に `provider status` / `model pull` / `model warmup` を success path で実行でき、warmup 前は `ollama ps` が空、warmup 後は `qwen2.5:7b` が loaded 状態になったため、warmup 完了による状態改善を確認できた。
- 合格: public surface、責務境界、進捗表示、終了コードは docs と実装で整合している。`provider status` / `model pull` / `model warmup` の parser と handler は [src/local_llm_benchmark/cli/main.py](../../src/local_llm_benchmark/cli/main.py) で設計どおり分離され、正準 JSON は [src/local_llm_benchmark/provider_preparation.py](../../src/local_llm_benchmark/provider_preparation.py) に集約されている。`provider status` は host facts や Model Candidate cross-check を持ち込まず、`model warmup` は `config dry-run` と分離された explicit execution のまま保たれている。
- 合格: 標準ライブラリ制約と既存 CLI 非破壊は確認できた。provider preparation 契約は [src/local_llm_benchmark/providers/base.py](../../src/local_llm_benchmark/providers/base.py) に型として追加され、Ollama 実装は [src/local_llm_benchmark/providers/ollama.py](../../src/local_llm_benchmark/providers/ollama.py) で `urllib` のみを使う。focused tests 46 件と run / compare 系 13 件が成功し、既存 CLI 回帰は見当たらない。
- 合格: negative path / success path のテストは十分に追加されている。CLI 側は [tests/test_cli_phase3.py](../../tests/test_cli_phase3.py) で provider status success / negative、model pull success、model warmup success / failure を検証し、adapter 側は [tests/test_providers.py](../../tests/test_providers.py) で status、already_present pull、progress 付き pull、warmup、unreachable probe を検証している。実機では negative path も設計どおりの終了コードと stdout / stderr 分離になっていた。

### 直接修正した範囲

- 本 reviewer task の Status、Related IDs、進捗ログ、レビュー記録を更新

### 差し戻し事項

- なし

### ユーザー報告可否

- 可。実装・テスト・live smoke に加え、前回 blocker だった README の user-facing 文言不整合も解消したため、reviewer 観点の blocker はない。ただし [progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md](progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md) を `done` に進めるには、progress ルール上、`review-pending` の子 task (TASK-00014-01 / 02 / 03) を `done` に確定させてから閉じる必要がある。