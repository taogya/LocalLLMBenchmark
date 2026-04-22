---
request_id: "00009"
task_id: "00009-05"
parent_task_id: "00009-00"
owner: "reviewer"
title: "review-roadmap-3-minimum-slice"
status: "done"
depends_on:
  - "00009-04"
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T01:27:25+09:00"
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

- ロードマップ 3 の最小スライスが過不足なく入っているか確認したい。

# 整理した要件

- prompt、評価、保存、テスト、docs の整合を確認する。

# 作業内容

- README、docs/architecture 2 件、configs/prompt_sets/core-small-model-ja-v1.toml、prompts 配下 6 prompt、src/local_llm_benchmark/benchmark/evaluation.py、src/local_llm_benchmark/benchmark/runner.py、src/local_llm_benchmark/storage/base.py、src/local_llm_benchmark/storage/jsonl.py、tests/benchmark/test_runner.py、tests/benchmark/test_evaluation.py、tests/storage/test_jsonl.py、tests/config/test_loader.py、tests/cli/test_main.py、tests/cli/test_live_smoke.py を確認した。
- progress/evaluation-analyst/00009-01-define-roadmap-3-minimum-scope.md、progress/prompt-analyst/00009-02-design-missing-sample-prompts.md、progress/solution-architect/00009-03-design-case-evaluation-output.md、progress/programmer/00009-04-implement-roadmap-3-minimum-slice.md を読み、request 00009 の acceptance と実装差分を照合した。
- manual、hybrid、similarity、rouge_like、factuality_check の混入有無を README、docs、prompts、benchmark、storage、tests に対して検索し、公式比較の出力実装が deterministic scorer のみを対象にしていることを確認した。
- get_errors で benchmark、storage、対象 tests の診断 0 件を確認した。
- source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.config.test_loader tests.benchmark.test_evaluation tests.benchmark.test_runner tests.storage.test_jsonl tests.cli.test_main tests.cli.test_live_smoke を再実行し、18 tests、OK、skipped=3 を確認した。
- 会話コンテキスト上の直近実行結果として、LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke が exit code 0 で完了していることも確認した。

# 判断

- 6 カテゴリ各 1 prompt は prompts 配下と configs/prompt_sets/core-small-model-ja-v1.toml でそろっており、prompt set から解決できる。
- 6 prompt の evaluation_reference と output_contract は、現行 deterministic scorer の参照方法と矛盾していない。label、text、json 参照が必要な prompt は machine-readable な evaluation_reference を持ち、reference_type が none の prompt は空 table で shape がそろっている。
- case-evaluations.jsonl は 1 case x 1 metric の行スキーマとして必要項目を満たし、run-metrics.json は run_id 配下で model_key x prompt_id x prompt_category scope の最小集計を保持している。
- runner は evaluation_mode が auto の条件だけを case-evaluations と run-metrics に流しており、manual または hybrid scorer は今回の公式比較へ混入していない。
- provider adapter 未登録など response を持たない error record は records.jsonl にのみ残り、case-evaluations と run-metrics.sample_count へ混ざらない。
- README と architecture docs の現在地記述は、6 prompt 構成、deterministic scorer、case-evaluations.jsonl、run-metrics.json の現行コードに追随している。
- 未解消の重大 finding は確認されなかった。

# 成果

## 確認対象

- README.md
- docs/architecture/prompt-and-config-design.md
- docs/architecture/benchmark-foundation.md
- configs/prompt_sets/core-small-model-ja-v1.toml
- prompts/classification/contact-routing-v1.toml
- prompts/extraction/invoice-fields-v1.toml
- prompts/rewrite/polite-rewrite-v1.toml
- prompts/summarization/meeting-notice-summary-v1.toml
- prompts/short_qa/support-hours-answer-v1.toml
- prompts/constrained_generation/followup-action-json-v1.toml
- src/local_llm_benchmark/benchmark/evaluation.py
- src/local_llm_benchmark/benchmark/runner.py
- src/local_llm_benchmark/storage/base.py
- src/local_llm_benchmark/storage/jsonl.py
- tests/benchmark/test_runner.py
- tests/benchmark/test_evaluation.py
- tests/storage/test_jsonl.py
- tests/config/test_loader.py
- tests/cli/test_main.py
- tests/cli/test_live_smoke.py

## 発見事項

- 未解消の重大 finding はなし。
- reviewer によるコード修正は不要と判断した。progress 更新のみ実施した。

## 残課題

- live smoke は通っているが、tests/cli/test_main.py と tests/cli/test_live_smoke.py は artifact の存在確認が中心で、case-evaluations.jsonl と run-metrics.json の metric 名や件数までは end-to-end で固定していない。
- 現行の最小スライスは deterministic な形式と制約の確認に寄せており、rewrite、summarization、constrained_generation の意味妥当性や内容忠実性は引き続き scope 外である。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、request 00009 の最小スライスは done として扱ってよい。

## 改善提案

- 次段階で golden result を 1 本追加し、case-evaluations.jsonl の metric 名、run-metrics.json の sample_count、scope を CLI 経路でも固定すると、runner と storage の配線崩れを早く検知しやすい。
- constrained_generation の比較を少し厳しくしたくなったら、channel の期待値も output_contract.required_values または evaluation_reference に追加し、現在の format と制約遵守中心の比較から段階的に広げるとよい。

# 次アクション

- project-master へ、重大 finding なし、追加修正なし、関連 unit test 再実行成功、live smoke 既存成功を引き継ぐ。

# 関連パス

- README.md
- docs/architecture
- prompts
- configs/prompt_sets
- src/local_llm_benchmark/benchmark
- src/local_llm_benchmark/storage
- tests