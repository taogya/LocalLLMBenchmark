# TASK-00014-02 provider status / model pull / model warmup 実装とテスト

- Status: done
- Role: programmer
- Parent: TASK-00014
- Related IDs: REQ-00001, FUN-00408, FUN-00409, FUN-00410, CLI-00112, CLI-00113, CLI-00114, CLI-00205, CLI-00309, PVD-00108, PVD-00109, PVD-00110, NFR-00001, NFR-00302, PROG-00103
- 起票日: 2026-04-24

## 目的

TASK-00014-01 で確定した仕様に基づき、`provider status` / `model pull` / `model warmup` を追加する。Run 実行前のコールドスタート起因ノイズを抑える導線を CLI 上に用意し、既存 `system-probe` / `config lint` / `config dry-run` / `run` の挙動は壊さない。

## 完了条件

- 着手時点で TASK-00014-01 が `done` になっている。
- `provider status` / `model pull` / `model warmup` が設計どおりの入力を受け、結果と終了コードを返す。
- pull の進捗と warmup 完了が、結果出力と分離された形でユーザーに視認できる。
- 既存 `system-probe` / `config lint` / `config dry-run` / `run` の public surface と既存テストに回帰がないことを確認している。
- 標準ライブラリ + 既存 Provider Adapter / probe 基盤の再利用で実装している。
- テスト結果と必要な検証手順が進捗ログに記録されている。

## スコープ外

- 設計文書更新 (TASK-00014-01)
- README 更新 (TASK-00014-03)
- reviewer による最終確認と実機 smoke (TASK-00014-04)

## 進捗ログ

- 2026-04-24 project-master: 起票。設計確定後に着手する待機 task として作成。
- 2026-04-24 project-master: 現行 trunk には `system-probe` / `config lint` / `config dry-run` があるため、既存責務を崩さず additive に実装すること、warmup 効果の実機確認は reviewer が担当することを共有。
- 2026-04-24 programmer: Status を `in-progress` として着手。[progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md](progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md), [progress/reviewer/TASK-00014-05-review-provider-cli-warmup-design.md](progress/reviewer/TASK-00014-05-review-provider-cli-warmup-design.md), [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/requirements/04-out-of-scope.md](docs/requirements/04-out-of-scope.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md), [src/local_llm_benchmark/cli/main.py](src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/providers/base.py](src/local_llm_benchmark/providers/base.py), [src/local_llm_benchmark/providers/ollama.py](src/local_llm_benchmark/providers/ollama.py), [src/local_llm_benchmark/system_probe.py](src/local_llm_benchmark/system_probe.py), [src/local_llm_benchmark/preflight.py](src/local_llm_benchmark/preflight.py) を確認し、既存 probe 契約を維持したまま explicit provider operation を adapter 境界へ追加するのが最小変更だと判断した。
- 2026-04-24 programmer: [src/local_llm_benchmark/provider_preparation.py](src/local_llm_benchmark/provider_preparation.py), [src/local_llm_benchmark/cli/main.py](src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/providers/base.py](src/local_llm_benchmark/providers/base.py), [src/local_llm_benchmark/providers/__init__.py](src/local_llm_benchmark/providers/__init__.py), [src/local_llm_benchmark/providers/ollama.py](src/local_llm_benchmark/providers/ollama.py), [tests/test_cli_phase3.py](tests/test_cli_phase3.py), [tests/test_providers.py](tests/test_providers.py) を更新し、`provider status` / `model pull` / `model warmup` を追加した。CLI は `provider status` と `model pull` / `model warmup` を group command として公開し、`provider_preparation.py` で JSON 正準形と Markdown 派生を生成、stdout には最終結果のみ、stderr には `provider status` の negative issue と `model pull` / `model warmup` の進捗 / 開始 / 完了通知のみを出すようにした。Provider Adapter には `status` / `pull` / `warmup` 契約を追加し、Ollama は `/api/version`, `/api/tags`, `/api/pull`, `/api/generate` の empty prompt load を標準ライブラリ `urllib` だけで実装した。`model pull` は inventory で既存 model を検知した場合 `already_present` を返し、`model warmup` は actual provider execution を 1 回だけ行う。
- 2026-04-24 programmer: focused validation を実施。`PYTHONPATH=src python -m unittest tests.test_providers` は 15 tests 成功、`PYTHONPATH=src python -m unittest tests.test_cli_phase3` は 31 tests 成功。整形修正後に `PYTHONPATH=src python -m unittest tests.test_providers tests.test_cli_phase3` を再実行し 46 tests 成功、さらに `PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_compare_integration tests.test_smoke_checklist tests.test_cli_phase3 tests.test_providers` を実行し 59 tests 成功を確認した。`get_errors` でも今回の変更ファイルに問題がないことを確認した。
- 2026-04-24 programmer: 実 CLI smoke として `PYTHONPATH=src python -m local_llm_benchmark.cli.main provider status --config-dir configs` を実行。ローカル Ollama 未起動環境では exit 9 (CLI-00309) となり、stdout は `providers` / `summary` の 2 セクション JSON、stderr は `[provider status] provider ... unreachable` の 1 行出力になり、`system-probe` と責務が交差していないことを確認した。
- 2026-04-24 programmer: `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行し、ID / progress / markdown / mermaid / role-boundary まで含む検証が全件 OK で完了した。
- 2026-04-24 programmer: 完了条件を満たしたため Status を `review-pending` に更新。reviewer は `provider status` と `system-probe` の責務分離、`model pull` の explicit 性と stdout/stderr 分離、`model warmup` が `config dry-run` を置換せず actual provider execution を 1 回だけ行う点、既存 `run` / `compare` / `check` / `system-probe` / `config lint` / `config dry-run` 非破壊を重点確認する。
- 2026-04-24 programmer: [progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md](progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md) で判定が合格、Status が `done` であることを確認した。reviewer 合格を受けて本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)