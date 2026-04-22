---
request_id: "00012"
task_id: "00012-03"
parent_task_id: "00012-00"
owner: "evaluation-analyst"
title: "assess-current-evaluation-method"
status: "done"
depends_on: []
created_at: "2026-04-18T19:20:00+09:00"
updated_at: "2026-04-18T20:10:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "src/local_llm_benchmark/benchmark/runner.py"
  - "src/local_llm_benchmark/benchmark/models.py"
  - "src/local_llm_benchmark/providers/ollama/client.py"
  - "src/local_llm_benchmark/providers/openai_compatible/client.py"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "tests/benchmark/test_evaluation.py"
---

# 入力要件

- 現在の評価アルゴリズムと、乱数影響をどこまで考慮しているかを整理したい。
- ユーザー説明で誤解されやすい点として、run gate、sample_count、provider ごとの seed 挙動も切り分ける。

# 整理した要件

- README、docs/architecture/prompt-and-config-design.md、src/local_llm_benchmark/benchmark/evaluation.py、tests/benchmark/test_evaluation.py を確認し、現行の scorer、metric、run 集計条件を洗い出した。
- src/local_llm_benchmark/benchmark/runner.py と src/local_llm_benchmark/benchmark/models.py を確認し、response がない record は records.jsonl に残るが auto 評価には流れないこと、generation snapshot に temperature、top_p、max_tokens、seed が保存されることを確認した。
- configs/benchmark_suites/local-three-tier-baseline-v1.toml を確認し、sample baseline suite が temperature 0.0、top_p 0.95、max_output_tokens 128、seed 7 を上書きすることを確認した。
- src/local_llm_benchmark/providers/ollama/client.py と src/local_llm_benchmark/providers/openai_compatible/client.py を確認し、Ollama は seed を request に送る一方、OpenAI-compatible v1 は seed を送らないことを確認した。
- README と docs/architecture/prompt-and-config-design.md に、現行評価方式、未採用手法、ランダム性の限界を明記した。
- ランダム性に対して今の構成がどこまで頑健か、何が未対応かを明示する。

# 作業内容
- 現行の公式評価は、category ごとに固定解決される deterministic scorer の閉じた集合として理解するのが最も正確である。
- scorer 自体は deterministic だが、LLM 応答の揺れを統計的に吸収する仕組みは未実装であり、ランダム性への頑健性は generation 条件の固定と task 設計に依存する。
- ユーザーへは、json_valid_rate / format_valid_rate のような運用 gate と、accuracy / macro_f1 / exact_match_rate のような比較指標を分けて説明する必要がある。
- 完走性の説明では、record_count と sample_count を分けないと誤解を招く。
- これから確認する。

# 判断
## 評価対象

### 現行評価の要約

- 現行の公式 auto 評価で使う scorer は、exact_match_label、exact_match_text、exact_match_json_fields、json_valid、constraint_pass、length_compliance、format_valid の 7 つだけである。
- category ごとの run metric は次のとおりである。
  - classification: accuracy、macro_f1
  - extraction: exact_match_rate、json_valid_rate
  - rewrite: constraint_pass_rate
  - summarization: length_compliance_rate
  - short_qa: exact_match_rate
  - constrained_generation: constraint_pass_rate、format_valid_rate
- case-evaluations.jsonl は 1 case x 1 metric の正本で、run-metrics.json は model_key x prompt_id x prompt_category 単位で mean または macro_f1 を集計する。
- response がない record、または evaluation_mode != auto の条件は、records.jsonl には残るが case-evaluations.jsonl と run-metrics.json には入らない。

### ランダム性に関する評価

- generation 条件は request snapshot に保存され、sample baseline suite では temperature 0.0、top_p 0.95、max_output_tokens 128、seed 7 を使う。
- scorer は deterministic なので、同じ normalized prediction と reference に対して判定はぶれない。
- ただし入力である LLM 応答の揺れを吸収する仕組みは未実装である。複数回実行、分散集計、自己一致投票、信頼区間、judge による再採点はない。
- seed の実効性は provider 依存である。Ollama は seed を request に送るが、OpenAI-compatible v1 は送らないため、同じ snapshot を保存しても provider によって再現性が揃わない。
- 現行方式が比較的頑健なのは、classification、extraction、short_qa のような単一正解寄り task と、rewrite / constrained_generation の明示制約チェックである。意味保持、要約品質、run 間分散は頑健に評価できない。

### 未採用手法の一覧

- レーベンシュタイン距離や一般的な文字列類似度
- ROUGE-like
- embedding 類似度
- LLM judge
- factuality_check、similarity、manual / hybrid の quality scorer

### ユーザーへ説明すべき注意点

- json_valid_rate は JSON parse 成功だけを見る。required_fields の一致や値の正確性は exact_match_rate、JSON object の key や型の妥当性は format_valid_rate と分けて読む必要がある。
- length_compliance_rate は文字数レンジだけを見る。要約としての意味妥当性は現行評価に含まれない。
- 現行の run gate が固定されているのは json_valid_rate >= 1.0 と format_valid_rate >= 1.0 だけで、それ以外は dataset 較正前の比較指標である。
- manifest の record_count と run-metrics の sample_count は別物である。実行失敗や auto 評価対象外 record があると一致しない。
- 現行の evaluation.conditions は category ごとにコードで固定解決されるため、新しい metric を公式評価へ追加するには prompt metadata だけではなく benchmark/evaluation.py 側の実装拡張が必要である。

## 推奨条件または推奨指標

- 現行ユーザー説明では、「完走性と形式妥当性は確認できるが、semantic quality と stochastic robustness はまだ確認できない」と明示するのが妥当である。
- モデル比較の主対象としては、temperature 0.0 かつ seed を実際に適用できる provider 上で、classification / extraction / short_qa を優先すると解釈が安定しやすい。
- rewrite と constrained_generation は制約遵守の比較、summarization は length_compliance の比較として扱い、意味品質の優劣までは主張しない方がよい。

## 根拠メモ

- benchmark/evaluation.py の scorer dispatch は 7 scorer だけを実装している。
- evaluate_record は response がない record を空評価として扱い、evaluation_mode = auto の条件だけを出力する。
- runner は error record も保存するが、case-evaluations と run-metrics の sample_count には含めない。
- baseline suite は generation 条件を強く固定するが、provider 実装の差で seed の扱いは揃っていない。

## 未解決事項

- run 間分散や seed 有効性を横断比較するための保存項目と集計方法は未定である。
- semantic quality を扱う scorer の較正用データ、閾値、manual / hybrid の責務境界は未整備である。
- provider ごとの seed 対応可否を、設定または manifest で明示する仕組みはまだない。

## 改善提案

- provider ごとに seed の適用可否を capability または manifest へ明示すると、再現性の説明がしやすい。
- ランダム性を評価対象に含める場合は、同一 case の複数回実行と分散集計を追加し、単発 run の score と分けて保存した方がよい。
- semantic quality を入れる場合は、manual / hybrid を evaluation_mode で明確に分離し、現行の deterministic metric と混ぜない方がよい。
- 未着手。

# 成果
- project-master は本整理を request 00012 の最終報告へ統合し、runtime 検証結果と合わせて説明する。
- reviewer は README と docs で、採用済み評価と未採用手法、provider 依存の seed 挙動が一貫しているかを確認する。
- 未着手。

# 次アクション

- 評価方式の要点と限界を整理する。

# 関連パス

- docs/architecture/prompt-and-config-design.md
- src/local_llm_benchmark/benchmark/evaluation.py