# TASK-00013-02 config lint / dry-run 実装とテスト

- Status: done
- Role: programmer
- Parent: TASK-00013
- Related IDs: REQ-00001, FUN-00406, FUN-00407, CLI-00110, CLI-00111, CLI-00308, CFG-00604, CFG-00605, CFG-00606, CFG-00607, NFR-00302, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00013-01 で確定した仕様に基づき、`config lint` / `config dry-run` を追加する。生成済み TOML の静的検証と、run.toml 起点の preflight を本実行なしで行えるようにし、既存 CLI の挙動は壊さない。

## 完了条件

- 着手時点で TASK-00013-01 が `done` になっている。
- `config lint` が設計どおりの入力を受け、静的整合性の検出結果と終了コードを返す。
- `config dry-run` が provider 疎通、指定モデル解決、1 case の prompt 組立までを設計どおりに実施し、実 inference は行わない。
- 既存 sample (`configs/run.toml` 等) で OK 判定が出ること、異常系の新規テストが追加されていることを確認している。
- 標準ライブラリ + 既存 Configuration Loader / Provider Adapter / Run 計画組立の再利用で実装している。
- テスト結果と必要な検証手順が進捗ログに記録されている。

## スコープ外

- 設計文書更新 (TASK-00013-01)
- README 更新 (TASK-00013-03)
- 最終レビュー (TASK-00013-04)

## 進捗ログ

- 2026-04-23 project-master: 起票。設計確定後に着手する待機 task として作成
- 2026-04-23 programmer: Status を `in-progress` に更新。正本 [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md), [progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md](progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md), [progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md](progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md) を確認し、`config lint` は Configuration Loader の単一ファイル解決追加、`config dry-run` は Run 計画組立と Provider probe 再利用で実装できると判断した。
- 2026-04-23 programmer: [src/local_llm_benchmark/config/loader.py](src/local_llm_benchmark/config/loader.py), [src/local_llm_benchmark/config/__init__.py](src/local_llm_benchmark/config/__init__.py), [src/local_llm_benchmark/cli/main.py](src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/orchestration/coordinator.py](src/local_llm_benchmark/orchestration/coordinator.py), [src/local_llm_benchmark/providers/base.py](src/local_llm_benchmark/providers/base.py), [src/local_llm_benchmark/providers/ollama.py](src/local_llm_benchmark/providers/ollama.py), [src/local_llm_benchmark/preflight.py](src/local_llm_benchmark/preflight.py) を更新し、`config lint` / `config dry-run` を `config` 配下に追加した。`config lint` は Task Profile / Model Candidate / Provider / Run / Comparison / config-dir を静的検証できるようにし、単一ファイル時は標準配置または明示指定の補助設定ソースを解決する。`config dry-run` は Run 設定起点で代表 1 Case を選び、Run と共通の request 組立、Provider Adapter の probe、request validate を再利用して `run` / `probe` / `prompt_check` / `summary` の 4 セクション JSON/Markdown を返し、CLI-00308 dry-run-negative を実装した。既存 `check` / `system-probe` / `run` は public surface と責務を変えていない。
- 2026-04-23 programmer: [tests/test_cli_phase3.py](tests/test_cli_phase3.py) を更新し、`config lint` の config-dir / 単一 Run / ModelCandidate 補助ソース不足 / Comparison 検証、`config dry-run` の JSON / Markdown / model negative / prompt negative を追加で検証した。
- 2026-04-23 programmer: 検証を実施。`PYTHONPATH=src python -m unittest tests.test_cli_phase3.TestConfigLintCommand tests.test_cli_phase3.TestCheckCommand` は 10 tests すべて成功。続けて `PYTHONPATH=src python -m unittest tests.test_cli_phase3` は 26 tests すべて成功し、既存 `check` / `system-probe` と新規 `config lint` / `config dry-run` の CLI 回帰なしを確認した。さらに `PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_providers` は 14 tests すべて成功し、request 組立共通化と Provider request validate 公開化が既存 run / provider 挙動を壊していないことを確認した。
- 2026-04-23 programmer: 実コマンドでサンプル設定を確認。`PYTHONPATH=src python -m local_llm_benchmark.cli.main config lint configs` と `PYTHONPATH=src python -m local_llm_benchmark.cli.main config lint configs/run.toml --config-dir configs` はどちらも「問題なし」。`PYTHONPATH=src python -m local_llm_benchmark.cli.main config dry-run configs/run.toml --config-dir configs` は Provider 未起動のため CLI-00308 を返し、`probe.provider_status=unreachable` と `prompt_check.status=ready` を確認した。
- 2026-04-23 programmer: 完了条件を満たしたため Status を `review-pending` に更新した。reviewer は `config lint` の単一ファイル補助ソース境界、`config dry-run` の 4 セクション出力と CLI-00308、既存 `check` / `system-probe` / `run` 非破壊を重点確認する。
- 2026-04-23 programmer: [progress/reviewer/TASK-00013-04-review-config-lint-dry-run.md](progress/reviewer/TASK-00013-04-review-config-lint-dry-run.md) が `done` かつ合格、差し戻し事項なしであることを確認し、Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)