---
request_id: "00009"
task_id: "00009-04"
parent_task_id: "00009-00"
owner: "programmer"
title: "implement-roadmap-3-minimum-slice"
status: "done"
depends_on:
  - "00009-01"
  - "00009-02"
  - "00009-03"
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T01:20:49+09:00"
related_paths:
  - "README.md"
  - "docs/architecture"
  - "prompts"
  - "configs/prompt_sets"
  - "src/local_llm_benchmark/benchmark"
  - "src/local_llm_benchmark/storage"
  - "tests"
---

# 入力要件

- ロードマップ 3 の最小スライスを実装したい。

# 整理した要件

- summarization / short_qa / constrained_generation の sample prompt を追加し、core-small-model-ja-v1 から 6 prompt を解決できる状態にする。
- 全 sample prompt を deterministic scorer と整合する evaluation_reference と output_contract にそろえる。
- scorer 実行と run 集計は benchmark 層に置き、storage は case-evaluations.jsonl / run-metrics.json の書き出し専任に保つ。
- docs と tests も最小差分で更新し、error case を含む回帰を追加する。

# 作業内容

- prompts/summarization、prompts/short_qa、prompts/constrained_generation に sample prompt 3 件を追加し、rewrite prompt に空の metadata.evaluation_reference を追加した。
- configs/prompt_sets/core-small-model-ja-v1.toml を 6 prompt 構成へ更新し、loader / CLI / live smoke の期待値を 18 case 前提へ更新した。
- src/local_llm_benchmark/benchmark/evaluation.py に deterministic scorer 実行 helper と run 集計 helper を追加し、classification、extraction、rewrite、summarization、short_qa、constrained_generation の fixed metric を case-evaluations / run-metrics へ落とせるようにした。
- src/local_llm_benchmark/benchmark/runner.py から各 record の評価を呼び出し、ResultSink へ case-evaluations と run-metrics を渡すようにした。
- src/local_llm_benchmark/storage/base.py、src/local_llm_benchmark/storage/stub.py、src/local_llm_benchmark/storage/jsonl.py を更新し、storage は新 artifact の直列化とファイル管理だけを担当する構成を維持した。
- README.md、docs/architecture/benchmark-foundation.md、docs/architecture/prompt-and-config-design.md を最小更新し、6 カテゴリ sample prompt と case-evaluations.jsonl / run-metrics.json を現行仕様として明記した。
- tests/benchmark/test_evaluation.py を追加し、既存 loader / CLI / runner / storage test を更新して request 00009 の最小 acceptance を押さえた。

# 判断

- macro_f1 は case row では exact_match_label の normalized prediction / reference を保持し、run 集計時だけ label_space を使って算出する形にした。storage 側へ label_space 解釈を持ち込まないためである。
- response を持たない error record は records.jsonl には残すが、case-evaluations と run-metrics の sample_count からは除外した。records と評価結果の責務を分けるためである。
- constrained_generation の sample prompt は JSON object に寄せ、constraint_pass と format_valid の両方を deterministic に判定できる shape を採用した。

# 成果

- 6 カテゴリ各 1 prompt がそろい、core-small-model-ja-v1 から classification、extraction、rewrite、summarization、short_qa、constrained_generation の 6 prompt を解決できるようになった。
- records.jsonl に加えて case-evaluations.jsonl と run-metrics.json を run ごとに出力し、model_key x prompt_id x prompt_category scope の deterministic 集計を保存できるようになった。
- benchmark 層に scorer 実行と集計を閉じ込め、storage は JSON 系 artifact の出力だけを担う構成を維持した。
- error case では records.jsonl のみが実行失敗を保持し、評価 artifact は空または sample_count 0 扱いになることを tests で固定した。

# 検証

- get_errors で変更した benchmark / storage / tests の診断を確認し、型絞り込みと行長の指摘を解消した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.config.test_loader tests.prompts.test_repository tests.cli.test_main tests.cli.test_live_smoke tests.benchmark.test_runner tests.benchmark.test_evaluation tests.storage.test_jsonl`
  - 20 tests, OK, skipped=3
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
  - 3 tests, OK, 75.117s

# 次アクション

- reviewer が deterministic only の境界、6 prompt の metadata 整合、case-evaluations / run-metrics の scope と error-path を最終確認する。

# 関連パス

- README.md
- docs/architecture
- prompts
- configs/prompt_sets
- src/local_llm_benchmark/benchmark
- src/local_llm_benchmark/storage
- tests