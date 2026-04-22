---
request_id: "00020"
task_id: "00020-01"
parent_task_id: "00020-00"
owner: "evaluation-analyst"
title: "verify-live-run-and-scope-json-split"
status: "done"
depends_on: []
created_at: "2026-04-19T14:10:00+09:00"
updated_at: "2026-04-19T15:05:00+09:00"
related_paths:
  - "README.md"
  - "configs/benchmark_suites/openai-compatible-minimal-v1.toml"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "configs/prompt_sets/minimal-readiness-ja-v1.toml"
  - "prompts/extraction/invoice-fields-v1.toml"
  - "prompts/constrained_generation/followup-action-json-v1.toml"
  - "tmp/results/openai-compatible-minimal-v1-20260419-131217"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/benchmark/test_evaluation.py"
  - "progress/project-master/00020-00-verify-lmstudio-live-run-and-start-json-strict-tolerant-split.md"
  - "progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md"
  - "progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md"
  - "progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md"
---

# 要件整理

- 実機 LM Studio run が OpenAI-compatible minimal readiness 成功として妥当か確認する。
- 次の roadmap として、JSON task に限った strict / tolerant split の最小 metric taxonomy を整理する。
- strict metric の既存意味と既存 metric 名は維持し、tolerant 側は別 metric 名で追加する。
- 対象カテゴリは extraction と constrained_generation のみとし、rewrite、sentence_count、prompt wording 変更、manual / hybrid scorer は今回の scope 外に置く。

# 作業内容

- manifest.json、run-metrics.json、records.jsonl、case-evaluations.jsonl を確認し、run 完了状態、sample_count、threshold の有無、response の実記録を照合した。
- benchmark suite、model registry、prompt set、README を確認し、openai-compatible-minimal-v1 が 1 model x 3 prompts の readiness 用最小 suite であり、正式比較用 suite ではないことを再確認した。
- evaluation.py を確認し、strict JSON 系 scorer が raw response に対して json.loads を直接行い、code fence 除去や prose 復元を行わないことを確認した。
- request 00014 の evaluation / prompt 分析を突き合わせ、fenced JSON fail を wrapper cleanliness と payload correctness の未分離として再整理した。

# 判断

## 評価対象

### 1. LM Studio live run artifact の妥当性

- 妥当である。manifest.json は status = completed、record_count = 3 で、records.jsonl には token usage と latency_ms を含む実応答が保存されているため、OpenAI-compatible local server 経由の live run artifact として扱ってよい。
- この run は configs/benchmark_suites/openai-compatible-minimal-v1.toml と README の説明どおり、OpenAI-compatible readiness 用の最小 suite であり、1 model x 3 prompts の導線確認として読むのが正しい。
- run-metrics.json と case-evaluations.jsonl では、classification、extraction、short_qa の全 auto metric row が生成され、invoice-fields-v1 は strict の exact_match_rate = 1.0、json_valid_rate = 1.0 で通過している。したがって、LM Studio 実機でも少なくとも最小 extraction case では raw JSON-only contract を満たせている。
- contact-routing-v1 の macro_f1 = 0.25 は 4 ラベル空間に対する 1 case 集計の結果であり、threshold も未設定なので readiness 失敗とは読まない。これは最小 suite の集計粒度由来の数値であり、run 成功判定を崩さない。
- ただし、この suite には constrained_generation が入っていないため、今回の live run から言えるのは OpenAI-compatible minimal readiness 成功までである。JSON strict / tolerant split の必要性そのものは request 00014 の fenced JSON fail 観測と合わせて判断するのが妥当である。

### 2. 最小実装対象カテゴリ

- extraction と constrained_generation のみを今回の最小対象カテゴリにするのが妥当である。
- classification は JSON object を返す prompt ではあるが、今回の論点である wrapper cleanliness と payload correctness の未分離は extraction と constrained_generation で先に顕在化しているため、scope を広げない方がよい。
- rewrite は JSON task ではなく、sentence_count explainability と required_phrase の意味づけが別論点なので混ぜない方がよい。

### 3. 推奨 metric taxonomy

- strict 側は既存の exact_match_rate、json_valid_rate、constraint_pass_rate、format_valid_rate をそのまま維持する。
- tolerant 側は、outer wrapper を最小限だけ剥がした payload を別 metric 名で採点し、strict fail の原因を wrapper cleanliness と payload correctness に分解して読めるようにする。
- 推奨する新規 metric 名と意味は次のとおり。
  - extraction: json_payload_valid_rate
    - 前後空白と単一の code fence wrapper だけを外した payload が JSON object として parse できる率。strict の json_valid_rate が落ちたとき、wrapper 汚染だけで落ちたのかを切り分ける。
  - extraction: payload_exact_match_rate
    - 同じ最小 unwrap 後に required_fields を exact match で採点する率。strict の exact_match_rate が 0.0 でも、payload 自体が reference と一致していたかを分けて読める。
  - constrained_generation: payload_format_valid_rate
    - 同じ最小 unwrap 後に required_keys、allowed_keys、field_types を検証した率。strict の format_valid_rate を raw response cleanliness から分離して、payload object の構造妥当性を見る。
  - constrained_generation: payload_constraint_pass_rate
    - 同じ最小 unwrap 後に required_values を JSON payload から検証し、required_phrases / forbidden_phrases は最小 unwrap 後の文字列に対して採点する率。strict の constraint_pass_rate が wrapper 由来で落ちたのか、payload 内容由来で落ちたのかを分けて読める。

### 4. strict fail を tolerant pass で上書きしない理由

- strict metric は raw response をそのまま downstream へ流せるかを見る既存 gate であり、運用上の意味がある。tolerant pass で上書きすると、この gate の信号が消えてしまう。
- strict fail かつ tolerant pass は、失敗が semantic failure ではなく wrapper cleanliness failure だったことを示す追加情報であり、既存 fail の取消しではない。
- compare / report は metric_name を opaque に扱える前提なので、strict と tolerant を並立させた方が互換性を保ったまま解釈を改善できる。

## 推奨条件または推奨指標

- tolerant 対象は extraction と constrained_generation に限定し、prompt category を明示して追加する。
- tolerant 側で許容する前処理は、前後空白除去と、レスポンス全体が単一 fenced block のときだけその wrapper を外す処理までに限定する。
- JSON の内部修復、先頭や末尾の prose 切り落とし、壊れた quote や comma の補修、key 名の推定補正、型 coercion は行わない。
- strict の threshold と pass/fail は変更しない。新規 tolerant metric に threshold を付けるとしても、strict gate とは別行で扱う。

## 根拠メモ

- openai-compatible-minimal-v1 は README と suite config で readiness 用の最小 suite と明記されている。
- records.jsonl の invoice-fields-v1 は raw response が bare JSON で保存され、case-evaluations.jsonl と run-metrics.json の strict extraction metric も 1.0 になっている。
- evaluation.py の _parse_json は raw json.loads のみであり、現行 strict scorer は fenced JSON を許容しない。
- request 00014 では Ollama run の invoice-fields-v1 と followup-action-json-v1 が fenced JSON により strict fail しつつ、payload 自体は概ね正しかったケースを確認済みである。
- README でも json_valid_rate、format_valid_rate、constraint_pass_rate は strict machine-readable JSON と lexical / structural contract-following を表し、wrapper 除去後の payload correctness は直接表さないと明記されている。

## 未解決事項

- live run artifact 自体には constrained_generation case がないため、payload_constraint_pass_rate と payload_format_valid_rate の必要性は request 00014 の fail 観測に依存している。
- metric 接頭辞は payload_ 系を第一推奨とするが、実装上 repo 全体で tolerant_ 接頭辞に統一したい事情があるなら命名だけは programmer / reviewer で最終調整してよい。ただし意味は payload correctness 側で固定する。

## 改善提案

- tolerant JSON 用の共通 helper は 1 つに寄せ、strict scorer とは別経路で最小 unwrap だけを行う方が実装とテストの説明がしやすい。
- unit test は bare JSON pass、fenced JSON pass、前後 prose 付き fail、壊れた JSON fail の 4 系統を最低限押さえるのがよい。
- README と architecture doc では、strict metric は raw response gate、payload 系 metric は最小 unwrap 後の diagnostic であることを並列表記すると解釈が安定する。

# 成果

- LM Studio 実機の openai-compatible-minimal-v1 run は、OpenAI-compatible minimal readiness 成功として妥当だと判断した。
- JSON task の strict / tolerant split は extraction と constrained_generation に限定して進めるのが最小であり、rewrite など別論点は切り離すべきだと整理した。
- strict metric を維持したまま追加する tolerant 側の最小 taxonomy と、strict fail を上書きしない理由、実装時の前処理上限を明文化した。

# 次アクション

- programmer は strict metric と threshold を変更せず、JSON task 向け payload 系 metric を最小追加する。
- reviewer は strict gate 互換性、命名の明確さ、README / docs の説明整合を確認する。
- 非スコープとして、rewrite の tolerant 評価、sentence_count 見直し、prompt wording 変更、manual / hybrid scorer 追加は今回扱わない。