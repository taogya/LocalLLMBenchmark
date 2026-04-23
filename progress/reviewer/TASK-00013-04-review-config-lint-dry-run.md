# TASK-00013-04 config lint / dry-run 最終確認

- Status: done
- Role: reviewer
- Parent: TASK-00013
- Related IDs: REQ-00001, FUN-00402, FUN-00404, FUN-00405, FUN-00406, FUN-00407, CLI-00105, CLI-00109, CLI-00110, CLI-00111, CLI-00308, NFR-00302, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00013 の設計・実装・README 更新を横断で確認し、`config lint` / `config dry-run` がモデル選定前のコンフィグ確認導線を補強しつつ既存 CLI を壊していないことを検証する。

## 完了条件

- 着手時点で TASK-00013-01 / 02 / 03 / 05 が `review-pending` または `done` になっている。
- public surface、責務境界、終了コード、異常系メッセージ、README 記述が相互に整合している。
- sample config の OK 判定と代表的な NG ケースが確認されている。
- 標準ライブラリ制約と既存 CLI 非破壊が確認されている。
- 必要な検証結果が親 task に引き継げる形で整理されている。

## スコープ外

- 追加実装そのもの
- README / docs の新規執筆

## 進捗ログ

- 2026-04-23 project-master: 起票。設計・実装・README 更新がそろった時点で最終確認を依頼予定
- 2026-04-23 reviewer: TASK-00013-01 / 05 が done、TASK-00013-02 / 03 が review-pending であることを確認し、対象 progress / README / docs / src / tests を横断確認した。`config lint` の単一ファイル / config-dir 両対応、`config dry-run` の provider 到達確認 / 指定 model 解決 / 代表 1 Case prompt 組立、`check` 既存互換、README 上の主導線、NFR-00302、既存 CLI 非破壊を確認した。`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK、`PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_run_integration tests.test_providers` は 40 tests すべて成功。sample config に対する `config lint configs` と `config lint configs/run.toml --config-dir configs` は「問題なし」、`config dry-run configs/run.toml --config-dir configs` は provider 未起動のため CLI-00308 (exit 8) で `probe.provider_status=unreachable`、`prompt_check.status=ready` を確認した。差し戻し事項なしとして Status を done に更新した。

## レビュー記録 (reviewer 用)

### 判定

- 合格

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

- OK: `PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_run_integration tests.test_providers` (40 tests)
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main config lint configs` → 「問題なし」
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main config lint configs/run.toml --config-dir configs` → 「問題なし」
- OK: `PYTHONPATH=src python -m local_llm_benchmark.cli.main config dry-run configs/run.toml --config-dir configs` → exit 8 (CLI-00308), `provider_status=unreachable`, `model_status=unknown`, `prompt_check.status=ready`

### 確認対象

- progress/reviewer/TASK-00013-04-review-config-lint-dry-run.md
- progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md
- progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md
- progress/programmer/TASK-00013-02-implement-config-lint-dry-run.md
- progress/docs-writer/TASK-00013-03-readme-config-lint-dry-run-update.md
- progress/project-master/TASK-00013-v1-2-0-config-lint-dry-run.md
- README.md
- docs/requirements/02-functional.md
- docs/design/02-components.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/config/loader.py
- src/local_llm_benchmark/preflight.py
- src/local_llm_benchmark/orchestration/coordinator.py
- src/local_llm_benchmark/providers/base.py
- src/local_llm_benchmark/providers/ollama.py
- tests/test_cli_phase3.py
- tests/test_run_integration.py
- tests/test_providers.py

### 発見事項

- 観点 1: 合格。README、docs/design、CLI 実装の public surface は `system-probe` → `config lint` → `config dry-run` → `run` で一致し、`check` は既存互換面として維持されている。`config lint` は静的整合性確認、`config dry-run` は Run 設定起点の preflight、`system-probe` は横断観測として責務が交差していない。`config dry-run` の終了コードは、設定不整合を CLI-00303、provider/model/prompt の preflight NG を CLI-00308 に分けており、実コマンドでも exit 8 と stderr 1 行 1 件表示が確認できた。
- 観点 2: 合格。`config lint` は config-dir と単一ファイルの両方を受け、単一ファイル時は標準配置または明示指定の補助設定ソースだけを解決する。`loader.py` の `lint_config_target` は Task Profile / Model Candidate / Provider / Run / Comparison の 5 種を分類し、Run は Task Profile / Model Candidate / Provider を、Comparison は store_root を要求する境界になっている。補助設定ソース不足を configuration error とする仕様は docs/design と実装・テストで一致している。
- 観点 3: 合格。`config dry-run` は `preflight.py` で `build_inference_request`、Provider Adapter の `probe`、`validate_request` を再利用し、provider 到達確認、指定 model 解決、代表 1 Case の prompt 組立可否までに留まる。`infer` 呼び出し、採点、Result Store 書込、host facts 収集は含まれず、`run` / `probe` / `prompt_check` / `summary` の 4 セクション出力も docs/design / README / テストで一致している。
- 観点 4: 合格。sample config では config-dir と run.toml 単体の `config lint` がいずれも OK。代表的な NG は `tests/test_cli_phase3.py` で補助設定ソース不足、model missing、prompt invalid、comparison 検証を確認しており、実コマンドでも Provider 未起動時に `config dry-run` が `probe.provider_status=unreachable`、`prompt_check.status=ready` を返して preflight NG を切り分けられている。
- 観点 5: 合格。実装は `argparse` / `tomllib` / `urllib` など標準ライブラリと既存コンポーネント再利用に留まり、新規依存はない。`tests.test_cli_phase3`、`tests.test_run_integration`、`tests.test_providers` の 40 tests が成功し、既存 `check` / `system-probe` / `run` の回帰は見当たらない。
- 補足: `get_errors` では `tests/test_providers.py` に line length 警告が 2 件残るが、機能・verify・テスト観点の blocker ではない。`python -m local_llm_benchmark.cli.main ...` で `runpy` RuntimeWarning も見えたが、README 既定の public surface は `local-llm-benchmark` であり、本 task の合否は変えない。

### 直接修正した範囲

- 本 reviewer task の Status、Related IDs、進捗ログ、レビュー記録を更新

### 差し戻し事項

- なし

### ユーザー報告可否

- 可。内容面では TASK-00013 は親 task を完了側へ進めてよい。進行管理上は TASK-00013-02 / 03 の状態反映が済み次第、project-master が親 task を `done` に更新できる。