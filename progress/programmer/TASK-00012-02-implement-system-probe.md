# TASK-00012-02 system-probe 実装とテスト

- Status: done
- Role: programmer
- Parent: TASK-00012
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-22

## 目的

TASK-00012-01 で確定した仕様に基づき、`local-llm-benchmark system-probe` を追加する。実行環境情報、Provider 疎通、モデル可用性を 1 コマンドで確認できるようにし、既存 CLI の挙動は壊さない。

## 完了条件

- 着手時点で TASK-00012-01 が `done` になっている。
- `local-llm-benchmark system-probe` が設計どおりに Markdown / JSON を出力する。
- 設定済み Provider への疎通結果と、`model_candidates.toml` に列挙されたモデルの可用性確認が実装されている。
- 既存 7 サブコマンドの動作・I/O に回帰がないことをテストで確認している。
- 標準ライブラリ + 既存 Provider Adapter のみで実装している。
- テスト結果と必要な検証手順が進捗ログに記録されている。

## スコープ外

- config lint / dry-run の実装や既存 `check` の責務拡張 (TASK-00013 側で扱う)
- README 更新 (TASK-00012-03)
- 最終レビュー (TASK-00012-04)

## 進捗ログ

- 2026-04-22 project-master: 起票。設計確定後に着手する待機 task として作成
- 2026-04-23 programmer: Status を `in-progress` に更新。正本 [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) と [progress/solution-architect/TASK-00012-01-design-system-probe.md](progress/solution-architect/TASK-00012-01-design-system-probe.md) を確認し、`system-probe` は `check` と分離した動的観測面として CLI Entry + Provider Adapter の追加実装で成立すると判断した。
- 2026-04-23 programmer: [src/local_llm_benchmark/system_probe.py](src/local_llm_benchmark/system_probe.py), [src/local_llm_benchmark/cli/main.py](src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/providers/base.py](src/local_llm_benchmark/providers/base.py), [src/local_llm_benchmark/providers/ollama.py](src/local_llm_benchmark/providers/ollama.py), [src/local_llm_benchmark/providers/__init__.py](src/local_llm_benchmark/providers/__init__.py) を更新し、`local-llm-benchmark system-probe` を追加した。JSON / Markdown 切替、`system` / `providers` / `model_candidates` / `summary` の 4 セクション、host facts の best-effort 収集、Provider Adapter 経由の到達確認 / model ref 解決、CLI-00307 の probe-negative 終了コード、stderr への 1 行 1 件 issue 表示を実装した。`check` は未変更で静的検証の責務に留めた。
- 2026-04-23 programmer: [tests/test_cli_phase3.py](tests/test_cli_phase3.py) と [tests/test_providers.py](tests/test_providers.py) を更新し、system-probe の JSON / Markdown / probe-negative と Ollama adapter の inventory probe を追加で検証した。
- 2026-04-23 programmer: 検証を実施。PYTHONPATH=src python -m unittest tests.test_providers tests.test_cli_phase3 は当初 default 引数束縛のため失敗したが [src/local_llm_benchmark/system_probe.py](src/local_llm_benchmark/system_probe.py) の adapter factory 遅延評価に修正後、29 tests すべて成功。続けて PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_compare_integration tests.test_smoke_checklist tests.test_cli_phase3 tests.test_providers を実行し、42 tests すべて成功して既存 7 サブコマンド回帰なしを確認した。
- 2026-04-23 programmer: MMDC_REQUIRED=1 bash scripts/verify.sh を実行し、check_id_format.py, check_id_uniqueness.py, check_id_references.py, check_doc_links.py, check_progress_format.py, check_mermaid_syntax.py, check_markdown_syntax.py, check_no_implementation_leak.py, check_role_boundary.py, check_oos_no_implementation.py がすべて OK。完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-23 programmer: [progress/reviewer/TASK-00012-04-review-system-probe.md](progress/reviewer/TASK-00012-04-review-system-probe.md) で判定が「合格」、Status が `done` であることを確認した。reviewer 合格を受けて本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)
