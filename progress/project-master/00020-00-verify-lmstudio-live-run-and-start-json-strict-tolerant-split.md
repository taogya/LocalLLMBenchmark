---
request_id: "00020"
task_id: "00020-00"
parent_task_id: null
owner: "project-master"
title: "verify-lmstudio-live-run-and-start-json-strict-tolerant-split"
status: "done"
depends_on: []
child_task_ids:
  - "00020-01"
  - "00020-02"
  - "00020-03"
created_at: "2026-04-19T14:10:00+09:00"
updated_at: "2026-04-19T15:20:00+09:00"
related_paths:
  - "tmp/results/openai-compatible-minimal-v1-20260419-131217"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/benchmark/test_evaluation.py"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/evaluation-analyst/00020-01-verify-live-run-and-scope-json-split.md"
  - "progress/programmer/00020-02-implement-json-tolerant-metrics.md"
  - "progress/reviewer/00020-03-review-json-tolerant-metrics.md"
---

# 入力要件

- ユーザーが LM Studio 実機で `openai-compatible-minimal-v1` を試行し、結果確認とロードマップ継続を求めている。
- 既存の OpenAI-compatible readiness 導線が実機で通るかを確定したい。
- 次のロードマップは、既存 strict 指標を壊さずに benchmark の解釈を改善する方向で進めたい。

# 整理した要件

- 必須要件は、`tmp/results/openai-compatible-minimal-v1-20260419-131217` を実機 LM Studio live 成功として記録すること。
- 必須要件は、次のロードマップを「JSON task の strict / tolerant split の最小スライス」に絞り、scope を明確化すること。
- 必須要件は、strict metric 名と strict gate の意味を維持したまま、wrapper cleanliness と payload correctness を別軸で読める tolerant metric の追加可否を判断し、可能なら実装まで進めること。
- 任意要件は、rewrite の tolerant quality や sentence_count explainability には今回広げず、別タスクへ残すこと。

# 作業内容

- project-master が live run artifact、既存 roadmap、evaluation 実装を再確認した。
- evaluation-analyst に、live run の妥当性確認と JSON strict / tolerant split の最小 metric taxonomy 整理を委譲する。
- programmer に、strict scorer を維持したまま tolerant JSON metric を追加し、テストと必要最小限の文書更新を行う実装を委譲する。
- reviewer に、strict gate の既存解釈を壊していないか、metric 命名と docs の整合が取れているかを確認させる。
- evaluation-analyst は `tmp/results/openai-compatible-minimal-v1-20260419-131217` を OpenAI-compatible minimal readiness 成功として妥当だと確認し、JSON task の最小 strict / tolerant split は extraction と constrained_generation に限定する方針を返した。
- programmer は strict metric 名と threshold を維持したまま、`json_payload_valid_rate`、`payload_exact_match_rate`、`payload_format_valid_rate`、`payload_constraint_pass_rate` を追加し、single fenced JSON の strict fail / payload pass 分離を unit test と文書まで含めて実装した。
- reviewer は重大 finding なしと判断し、strict gate の意味が維持され、payload metric は wrapper cleanliness と payload correctness を読む diagnostic として分離できていることを確認した。

# 判断

- `openai-compatible-minimal-v1` の live 通過により、OpenAI-compatible readiness の最小導線は blocker ではなくなった。
- 次の優先度は、strict fail を semantic failure と誤読しにくくする解釈改善であり、最小スライスは JSON task の strict / tolerant split である。
- rewrite の自然さ評価や sentence_count explainability は論点が別であり、今回の request へ混ぜない方が責務境界が明確である。
- strict 側は raw response gate として維持し、payload 側は前後空白除去と単一 fenced block unwrap だけを許す追加 diagnostic とするのが最小で妥当である。
- compare / report / storage は metric_name を opaque に扱う既存設計のままで新規 row を受け入れられるため、今回の split は既存 surface を壊さずに入れられる。

# 成果

- request 00020 を起票した。
- 実機 LM Studio run 成功を roadmap 継続判断の前提として固定した。
- JSON strict / tolerant split の最小スライスとして、extraction に `json_payload_valid_rate` と `payload_exact_match_rate`、constrained_generation に `payload_format_valid_rate` と `payload_constraint_pass_rate` を追加した。
- `README.md` と `docs/architecture/benchmark-foundation.md` に、strict gate と payload diagnostic の違い、前処理上限、strict fail を上書きしないことを追記した。
- `tests/benchmark/test_evaluation.py` に、bare JSON 正常系、single fenced JSON の strict fail / payload pass 分離、prose 混在 fail、aggregate 反映を追加した。
- reviewer 時点で重大 finding はなく、diagnostics 0 件、`tests.benchmark.test_evaluation` 5 tests, OK、`tests.benchmark.test_runner tests.benchmark.test_evaluation` 7 tests, OK を確認した。

# 次アクション

- 次に手を入れる候補は、1) payload 系の broken JSON fail を固定する専用回帰 test、2) compare / report 上で strict row と payload row の読みやすさ補助、3) rewrite / sentence_count 系の別 request 化、の順で検討できる。
- 今回の非スコープとして、rewrite の tolerant 評価、sentence_count explainability 改善、prompt wording 変更、manual / hybrid scorer 追加は据え置く。