---
request_id: "00013"
task_id: "00013-01"
parent_task_id: "00013-00"
owner: "programmer"
title: "rerun-ollama-live-checks"
status: "done"
depends_on: []
created_at: "2026-04-18T21:00:00+09:00"
updated_at: "2026-04-18T15:14:09+09:00"
related_paths:
  - "README.md"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "tests/cli/test_live_smoke.py"
  - "progress/project-master/00013-00-ollama-retest-and-openai-compatible-prep.md"
  - "tmp/runtime-checks/request-00013-20260418-151043"
---

# 入力要件

- Ollama 起動後の再テストを行い、success-path の完走可否を確認する。
- 評価レポートの結果が問題ないかを確認する。
- OpenAI-compatible 確認とは別件であることを切り分けられる材料を残す。

# 整理した要件

- 既存の opt-in live smoke と、README の suites -> run -> report 経路で Ollama の environment readiness を再確認する。
- success-path が完走しても metric fail は起こりうるため、artifact と case-evaluations まで見て report の妥当性を確認する。
- 失敗 metric があれば、接続失敗ではなく出力形式や制約不一致などの内容起因かを切り分ける。

# 作業内容

- 関連ファイルとして `README.md`、`configs/benchmark_suites/local-three-tier-baseline-v1.toml`、`tests/cli/test_live_smoke.py`、`src/local_llm_benchmark/cli/main.py`、`src/local_llm_benchmark/cli/report.py`、親タスク記録を確認した。
- Ollama 応答確認として次を実行し、CLI と API の両方が利用可能で、sample suite の 3 モデルがローカルに存在することを確認した。
  - `source .venv/bin/activate && command -v ollama && curl -fsS http://localhost:11434/api/version && ollama list`
- opt-in live smoke を次で実行し、3 tests が 101.530 秒で成功した。
  - `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
- README の CLI 導線を persistent artifact 付きで次の順に実行した。
  - `source .venv/bin/activate && local-llm-benchmark suites --config-root configs`
  - `source .venv/bin/activate && local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs`
  - `source .venv/bin/activate && local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id request-00013-20260418-151043 --output-dir tmp/runtime-checks`
  - `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/runtime-checks/request-00013-20260418-151043`
- 生成された `manifest.json`、`run-metrics.json`、`case-evaluations.jsonl`、`raw/` を確認し、metric fail の原因を artifact ベースで切り分けた。
- progress 以外のファイル編集は行っていない。

# 判断

- Ollama 側の environment readiness は確認できた。`curl http://localhost:11434/api/version` が成功し、`ollama list` で `gemma3:latest`、`qwen2.5:7b`、`llama3.1:8b` が見えている。
- success-path 自体は完走した。live smoke 3 件成功、README の `suites` -> `run` -> `report` もすべて成功し、`run` は `records: 18`、`success: 18`、`errors: 0` だった。
- report は構造的に妥当である。`manifest.json` の `record_count=18`、`run-metrics.json` の `metric_rows=27`、`raw/` の 18 ファイルが整合しており、`report` CLI も正常表示した。
- ただし metric は全通過ではない。失敗は接続や保存の問題ではなく、各モデル出力が現行 deterministic scorer の制約に合わなかったことが原因である。
- `classification` の `accuracy=1.0` に対して `macro_f1=0.25` なのは異常ではなく、現行 sample が 1 case かつ `label_space` が 4 ラベルであるため、macro 平均では 0.25 になる挙動と整合している。
- `n=1` の単一ケース評価なので、今回の report は「完走性と形式妥当性の確認」には有効だが、統計的に安定したモデル比較にはまだ弱い。
- OpenAI-compatible 確認を今回と切り分けるべき理由は、現行 suite と live smoke が `ollama` provider を前提にしており、OpenAI-compatible は別 server、別 model alias、場合によっては別 suite / model registry 準備が必要なためである。

# 成果

## 実行したコマンド

- `source .venv/bin/activate && command -v ollama && curl -fsS http://localhost:11434/api/version && ollama list`
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
- `source .venv/bin/activate && local-llm-benchmark suites --config-root configs`
- `source .venv/bin/activate && local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs`
- `source .venv/bin/activate && local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id request-00013-20260418-151043 --output-dir tmp/runtime-checks`
- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/runtime-checks/request-00013-20260418-151043`

## 何が通ったか

- Ollama API の `version` 応答成功。version は `0.20.7`。
- `ollama list` 成功。必要 3 モデルはすべて存在。
- live smoke 3 件成功。
  - `test_suites_lists_available_suite`
  - `test_suites_shows_target_suite_detail`
  - `test_run_writes_result_artifacts`
- README の `suites` -> `run` -> `report` 経路が完走。
- `run` は `records: 18`、`success: 18`、`errors: 0`。
- `report` は `metric_rows: 27` を表示し、artifact 読み出しに失敗しなかった。

## 生成された artifact

- run directory: `tmp/runtime-checks/request-00013-20260418-151043`
- 生成物:
  - `manifest.json`
  - `records.jsonl`
  - `case-evaluations.jsonl`
  - `run-metrics.json`
  - `raw/` 配下 18 ファイル

## report の要点

- `local.entry.gemma3`
  - classification: `accuracy=1.000`, `macro_f1=0.250`
  - extraction: `exact_match_rate=0.000`, `json_valid_rate=0.000` で fail
  - rewrite: `constraint_pass_rate=0.000`
  - summarization: `length_compliance_rate=1.000`
  - short_qa: `exact_match_rate=1.000`
  - constrained_generation: `constraint_pass_rate=0.000`, `format_valid_rate=0.000` で fail
- `local.balanced.qwen2_5`
  - classification: `accuracy=1.000`, `macro_f1=0.250`
  - extraction: `exact_match_rate=1.000`, `json_valid_rate=1.000` で pass
  - rewrite: `constraint_pass_rate=1.000`
  - summarization: `length_compliance_rate=1.000`
  - short_qa: `exact_match_rate=1.000`
  - constrained_generation: `constraint_pass_rate=0.000`, `format_valid_rate=0.000` で fail
- `local.quality.llama3_1`
  - classification: `accuracy=1.000`, `macro_f1=0.250`
  - extraction: `exact_match_rate=1.000`, `json_valid_rate=1.000` で pass
  - rewrite: `constraint_pass_rate=0.000`
  - summarization: `length_compliance_rate=0.000`
  - short_qa: `exact_match_rate=1.000`
  - constrained_generation: `constraint_pass_rate=1.000`, `format_valid_rate=1.000` で pass

## 失敗した場合の原因切り分け

- `local.entry.gemma3 / invoice-fields-v1`
  - `case-evaluations.jsonl` では `parse_error = "Expecting value at line 1 column 1"`。
  - 実出力が fenced code block 付き JSON だったため、`json_valid` と `exact_match_json_fields` の両方で落ちている。
- `local.entry.gemma3 / polite-rewrite-v1`
  - `failed_constraints = ["required_phrase:少々お待ちください", "sentence_count"]`。
  - 指定必須句を満たさず、引用符付き応答が sentence split 上 2 文扱いになっている。
- `local.entry.gemma3 / followup-action-json-v1`
  - `required_values_error` と `format_errors = ["invalid_json"]`。
  - fenced code block 付き JSON で、`required_values` と `format_valid` の両方が失敗。
- `local.balanced.qwen2_5 / followup-action-json-v1`
  - `local.entry.gemma3` と同じく fenced code block 付き JSON により `invalid_json`。
- `local.quality.llama3_1 / polite-rewrite-v1`
  - `failed_constraints = ["required_phrase:少々お待ちください"]`。
  - 丁寧な書き換え自体はできているが、required phrase の完全一致を満たしていない。
- `local.quality.llama3_1 / meeting-notice-summary-v1`
  - `observed_length = 73` で `min_chars = 80` を下回る。
  - 要約内容ではなく length_compliance 条件で落ちている。

## 補足

- `macro_f1=0.25` は 1 case x 4 ラベル空間の sample による値で、accuracy 1.0 と矛盾しない。
- 今回の run は success-path 完走確認としては成功だが、`n=1` なので品質比較の代表値としてはまだ粗い。

# 次アクション

- project-master が本結果を親タスクへ統合し、ユーザー向けに「Ollama の success-path は完走、OpenAI-compatible は別準備が必要」と整理して返す。
- OpenAI-compatible を live 確認する場合は、今回の Ollama suite とは別に server 起動、利用可能 model alias、必要なら `api_key_env` を満たす profile / suite 準備を行う。

# 関連パス

- README.md
- configs/benchmark_suites/local-three-tier-baseline-v1.toml
- tests/cli/test_live_smoke.py