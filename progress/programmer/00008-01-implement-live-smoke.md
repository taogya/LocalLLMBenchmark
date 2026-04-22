---
request_id: "00008"
task_id: "00008-01"
parent_task_id: "00008-00"
owner: "programmer"
title: "implement-live-smoke"
status: "done"
depends_on: []
created_at: "2026-04-18T12:50:00+09:00"
updated_at: "2026-04-18T00:44:27+09:00"
related_paths:
  - "README.md"
  - "docs/ollama/api-check.md"
  - "tests/cli/test_live_smoke.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_suite_catalog.py"
---

# 入力要件

- success-path smoke を実装し、README / docs の最小更新まで進める。

# 整理した要件

- `suites` -> `run` の流れを README 記載に沿って確認できる opt-in live smoke とする。
- 通常の unittest 実行では走らず、環境変数で明示的に有効化したときだけ live 実行する。
- live smoke では `suites --config-root configs`、`suites local-three-tier-baseline-v1 --config-root configs`、`run --config-root configs --suite local-three-tier-baseline-v1 --run-id ... --output-dir ...` を確認し、`manifest.json`、`records.jsonl`、`raw/` の生成まで見る。
- README と docs/ollama/api-check.md には、opt-in smoke の実行方法だけを短く追記する。

# 作業内容

- tests/cli/test_live_smoke.py を追加し、`LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE` が truthy のときだけ有効になる live smoke を実装した。
- live smoke の事前確認として provider profile から Ollama 接続先を読み、`OllamaClient` で version / tags を確認し、Ollama 未起動や必要モデル不足のときは理由付きで skip するようにした。
- smoke 本体では suites 一覧、suite 詳細、run の 3 テストを追加し、run では一時出力先配下の `manifest.json`、`records.jsonl`、`raw/` と raw ファイル生成まで確認するようにした。
- README.md では suite 詳細コマンドの説明を実態に合わせて最小修正し、opt-in smoke の実行コマンドを短く追記した。
- docs/ollama/api-check.md に opt-in live smoke 節を追加し、確認対象コマンドと skip 条件を短く追記した。

# 判断

- 共通 CLI や provider 非依存層には provider 固有コマンドを持ち込まず、live 環境の前提確認は test 側に閉じ込めた。
- opt-in 条件は単純な環境変数 1 つに寄せ、通常の unit test 実行では class 全体が skip される構成にした。
- required models は config bundle と model registry から解決し、sample suite の設定変更に追従できるようにした。

# 成果

- README 記載の `suites` -> `run` 導線をそのまま確認できる live smoke が追加された。
- 通常の unittest 実行では live smoke が 3 skip として扱われ、既存 unit test を壊さない状態を確認できた。
- Ollama 実環境では success-path smoke が通り、suite discovery から結果保存物生成まで確認できた。

# 検証

- `get_errors` で README.md、docs/ollama/api-check.md、tests/cli/test_live_smoke.py の診断を確認し、live smoke ファイル末尾の改行不足を修正した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.config.test_loader tests.cli.test_main tests.cli.test_suite_catalog tests.cli.test_live_smoke tests.storage.test_jsonl tests.benchmark.test_runner tests.prompts.test_repository tests.providers.test_ollama_adapter`
  - 19 tests, OK, skipped=3
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
  - 3 tests, OK, 104.569s

# 次アクション

- reviewer が opt-in 条件、README / docs 導線、実環境 live smoke 成功を最終確認する。

# 関連パス

- README.md
- docs/ollama/api-check.md
- tests/cli/test_live_smoke.py
- tests/cli/test_main.py
- tests/cli/test_suite_catalog.py