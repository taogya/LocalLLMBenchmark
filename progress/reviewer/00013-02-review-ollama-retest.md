---
request_id: "00013"
task_id: "00013-02"
parent_task_id: "00013-00"
owner: "reviewer"
title: "review-ollama-retest"
status: "done"
depends_on:
  - "00013-01"
created_at: "2026-04-18T21:20:00+09:00"
updated_at: "2026-04-18T17:23:13+09:00"
related_paths:
  - "README.md"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "tests/cli/test_live_smoke.py"
  - "progress/programmer/00013-01-rerun-ollama-live-checks.md"
  - "tmp/runtime-checks/request-00013-20260418-151043"
---

# 入力要件

- Ollama 起動後の再テスト結果を reviewer 観点で最終確認する。
- success-path 完走可否と report の読み解きが妥当か確認する。
- OpenAI-compatible 側を今回の確認範囲からどう切り分けるべきかも確認する。

# 整理した要件

- programmer が残した実行結果と artifact の読み解きが妥当かを確認する。
- 必要なら重大 finding を優先して整理し、なければその旨を明記する。
- ユーザー報告前提で、Ollama 完走確認と OpenAI-compatible の別準備要否が一貫して説明できるかを確認する。
- progress/reviewer/00013-02-review-ollama-retest.md を done に更新し、確認結果を次担当へ引き継げる形にする。

# 作業内容

- progress/programmer/00013-01-rerun-ollama-live-checks.md と progress/project-master/00013-00-ollama-retest-and-openai-compatible-prep.md を読み、今回の必須範囲と programmer の主張を照合した。
- README.md、configs/benchmark_suites/local-three-tier-baseline-v1.toml、tests/cli/test_live_smoke.py を確認し、sample suite と live smoke が Ollama の `local-three-tier-baseline-v1` を前提に `suites -> run -> report` を通す設計であることを確認した。
- tmp/runtime-checks/request-00013-20260418-151043 配下の manifest.json、run-metrics.json、case-evaluations.jsonl、records.jsonl、raw/ を確認し、completed run としての整合性、metric fail の原因、保存不良の有無を確認した。
- src/local_llm_benchmark/benchmark/evaluation.py と prompts/classification/contact-routing-v1.toml を確認し、`macro_f1=0.25` の説明が 4 ラベル固定の macro 平均実装と整合することを確認した。
- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/runtime-checks/request-00013-20260418-151043` を reviewer として再実行し、`records: 18`、`metric_rows: 27`、各 fail 行の表示内容が artifact と一致することを確認した。

# 判断

- Ollama success-path は、request 00013 の保存済み run について「完走した」と判断してよい。`manifest.json` は `status = completed`、`record_count = 18` で、records.jsonl の 18 record はすべて `error = null`、raw/ 配下も 18 ファイルそろっているため、接続不能や保存欠落で途中終了した run ではない。
- report の fail は接続不良や保存不良ではなく、deterministic scorer 条件起因と判断してよい。`case-evaluations.jsonl` には fenced code block による `parse_error`、required phrase 不一致、文字数条件未達など、各失敗の理由が case 単位で残っている。
- `macro_f1=0.25` の説明に破綻はない。classification prompt は label_space が 4 ラベル固定で、実装も label_space 全体に対する macro F1 を平均するため、1 case だけ正解した run では `1.0, 0.0, 0.0, 0.0` の平均として 0.25 になる。
- OpenAI-compatible を今回の request 範囲外として切り分けてよい。README は既定 sample suite が Ollama 前提であることを明記しており、local-three-tier-baseline-v1 も 3 つの local model key を固定選択している。OpenAI-compatible の success-path は別 server、別 model alias、必要なら別 provider profile 準備を前提にするため、今回の Ollama 再テストとは別確認である。
- 重大な blocking finding はない。ただし今回の run は各 prompt 1 case のため、品質比較の代表値ではなく、完走性と scorer/readout の妥当性確認として解釈するのが適切である。

# 成果

## 確認対象

- progress/programmer/00013-01-rerun-ollama-live-checks.md
- progress/project-master/00013-00-ollama-retest-and-openai-compatible-prep.md
- README.md
- configs/benchmark_suites/local-three-tier-baseline-v1.toml
- tests/cli/test_live_smoke.py
- tmp/runtime-checks/request-00013-20260418-151043/manifest.json
- tmp/runtime-checks/request-00013-20260418-151043/run-metrics.json
- tmp/runtime-checks/request-00013-20260418-151043/case-evaluations.jsonl
- tmp/runtime-checks/request-00013-20260418-151043/records.jsonl
- tmp/runtime-checks/request-00013-20260418-151043/raw/
- src/local_llm_benchmark/benchmark/evaluation.py
- prompts/classification/contact-routing-v1.toml

## 発見事項

- 未解消の重大 finding はなし。
- `report` の fail は artifact 欠落や transport error ではなく、現行 deterministic scorer が期待する JSON / 制約 / 長さ条件にモデル出力が一致しなかったことに起因している。
- `macro_f1=0.25` は sample の 1 case 評価と 4 ラベル固定の macro 平均から自然に出る値で、accuracy 1.0 と矛盾しない。
- reviewer によるコードまたは docs の修正は不要で、progress 更新のみ実施した。

## 残課題

- 現行 sample は各 prompt 1 case のため、今回の数値はモデル品質の安定比較ではなく、success-path と report 読み解き確認に限定して扱うのが妥当である。
- OpenAI-compatible local server の success-path は未確認であり、別 request で server 起動、model alias、provider profile / suite 準備を含めて確認する必要がある。

## ユーザー報告可否

- 可能。Ollama の recorded success-path 完走、report fail の原因、OpenAI-compatible の今回の範囲外という整理は一貫しており、重大なブロッカーは見当たらない。

## 改善提案

- OpenAI-compatible を次に確認するなら、`provider_id = "openai_compatible"` の model を含む最小 suite か opt-in smoke を別 request で用意し、今回の Ollama suite と混線しないようにする。
- classification の `macro_f1` を誤読しにくくするには、将来の比較 request で 1 prompt あたり複数 case を追加し、単一正例依存の値から早めに脱却するとよい。

# 検証

- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/runtime-checks/request-00013-20260418-151043`
  - `records: 18`、`metric_rows: 27`、各 metric row の threshold / passed / n 表示が artifact と一致

# 次アクション

- project-master へ、重大 finding なし、Ollama recorded success-path は完走扱い可、report fail は deterministic scorer 条件起因、OpenAI-compatible は今回の request 範囲外という結果を引き継ぐ。

# 関連パス

- README.md
- configs/benchmark_suites/local-three-tier-baseline-v1.toml
- tests/cli/test_live_smoke.py
- progress/programmer/00013-01-rerun-ollama-live-checks.md
- tmp/runtime-checks/request-00013-20260418-151043