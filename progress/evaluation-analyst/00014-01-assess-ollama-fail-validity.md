---
request_id: "00014"
task_id: "00014-01"
parent_task_id: "00014-00"
owner: "evaluation-analyst"
title: "assess-ollama-fail-validity"
status: "done"
depends_on: []
created_at: "2026-04-18T22:00:00+09:00"
updated_at: "2026-04-18T23:00:00+09:00"
related_paths:
  - "README.md"
  - "tmp/runtime-checks/request-00013-20260418-151043/case-evaluations.jsonl"
  - "tmp/runtime-checks/request-00013-20260418-151043/records.jsonl"
  - "tmp/runtime-checks/request-00013-20260418-151043/raw/00003-local.entry.gemma3-polite-rewrite-v1.json"
  - "prompts/rewrite/polite-rewrite-v1.toml"
  - "prompts/constrained_generation/followup-action-json-v1.toml"
  - "prompts/extraction/invoice-fields-v1.toml"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/benchmark/test_evaluation.py"
---

# 入力要件

- request 00013 の Ollama run で出た fail case を整理し、現在の評価結果が benchmark として妥当か判断する。
- fail を減らすこと自体を目的にせず、測定対象に対して条件が過不足ないかを整理する。

# 整理した要件

- case-evaluations.jsonl、records.jsonl、raw response、対象 prompt、README の評価説明、evaluation.py、関連テストを確認し、fail が prompt 契約違反か、semantic quality の不足かを切り分ける。
- JSON 系 task は downstream へそのまま流せる strict contract の評価として妥当か、rewrite は strict lexical instruction-following の評価として妥当かを分けて判断する。
- 現状結果を benchmark として許容できる解釈範囲と、そこから先に言い過ぎになる解釈範囲を明示する。
- 条件見直しは fail を消すためではなく、strict contract と tolerant quality を分離して benchmark の意味を明確にする方向で整理する。

# 作業内容

- gemma3 の invoice-fields-v1 は、field 内容自体は reference と一致する JSON を fenced code block 付きで返しており、raw parse 失敗により exact_match_rate と json_valid_rate の両方が 0.0 になっていることを確認した。
- gemma3 と qwen2.5 の followup-action-json-v1 は、required_keys と required_values を満たす内容を fenced code block 付きで返しており、format_valid_rate と constraint_pass_rate が raw parse 失敗で 0.0 になっていることを確認した。llama3.1 は bare JSON で通過している。
- qwen2.5 の polite-rewrite-v1 は exact phrase と 1 文条件を満たして pass した一方、llama3.1 は「しばらくお待ちください」、gemma3 は「少々お時間を頂戴できますでしょうか」を返し、natural だが lexical contract 不一致で fail していることを確認した。
- gemma3 の rewrite artifact は records.jsonl と raw response では見た目上 1 文だが、case-evaluations.jsonl では observed_sentence_count = 2 と記録されており、sentence_count 判定の説明可能性が弱いことを確認した。
- evaluation.py は JSON 系を raw json.loads で直接 parse し、code fence 除去を行わない。rewrite の constraint_pass は required_phrase の部分文字列判定と sentence_count の句読点ベース判定で採点する。テストは strict success path を押さえているが、fenced JSON 許容や quoted single sentence の edge case は押さえていない。

# 確認ポイント

- JSON fenced code block による fail は、現行 benchmark の目的に照らして妥当な fail か。
- required phrase と sentence_count による rewrite fail は、意図した instruction-following 測定か、過度に brittle か。
- 現在の結果を「問題ない」と言える範囲と言えない範囲を分ける。
- 条件見直しをするなら、fail を消すためではなく benchmark の意味を明確にする変更としてどう切り出すべきか提案する。

# 判断

## 評価対象

### 1. fenced code block による JSON fail の妥当性

- 妥当である。invoice-fields-v1 と followup-action-json-v1 は prompt 本文で JSON のみを返すよう明示し、README でも json_valid_rate と format_valid_rate を downstream へそのまま流せるかを見る運用 gate として位置付けている。
- 現行 scorer は raw response をそのまま json.loads し、code fence を除去しない。そのため fenced code block は現行 benchmark の意味では format violation であり、scorer の偶発的 fail ではない。
- ただし解釈範囲は限定が必要である。gemma3 の invoice-fields-v1 は payload 自体は正しいため、この fail から言えるのは「strict JSON-only contract を守れなかった」であって、「請求情報を抽出できなかった」ではない。現行 exact_match_rate は parse 成功を前提にしており、payload correctness と transport wrapper が結合している。

### 2. exact required phrase と sentence_count による rewrite fail の妥当性

- required_phrase fail は、strict instruction-following 測定としては妥当である。prompt は 1 文と exact phrase を明示し、README でも rewrite は constraint_pass_rate により明示制約を守れるかを見る task と説明している。
- したがって llama3.1 の「しばらくお待ちください」や gemma3 の「少々お時間を頂戴できますでしょうか」は、natural で意味も近いが、現行 benchmark では lexical contract 不一致として fail 扱いでよい。
- 一方で sentence_count は妥当性が弱い。contract 自体は structural constraint として理解できるが、gemma3 の raw output は見た目上 1 文なのに observed_sentence_count = 2 と記録されており、artifact 単体から判定根拠を説明しにくい。したがって sentence_count は現状では brittle な heuristic として扱うのが妥当であり、強い品質主張の根拠にはしにくい。
- gemma3 の case は required_phrase 単独でも fail なので、run 全体としての rewrite fail 自体は擁護できる。ただし sentence_count fail まで含めて強く断定するのは避けた方がよい。

### 3. 現状の結果を「問題ない」と言える範囲と言えない範囲

- 問題ないと言える範囲は、現行 run が strict machine-readable JSON と explicit lexical / structural constraint の遵守差を測る benchmark として動いている、という範囲である。
- 問題ないと言える範囲は、gemma3 と qwen2.5 の followup-action-json-v1 fail を「downstream-ready JSON gate を満たさなかった」と読むこと、gemma3 の invoice-fields-v1 fail を「machine-readable extraction contract を満たさなかった」と読むこと、rewrite fail を「exact phrase を含む strict contract を守れなかった」と読むことである。
- 問題ないと言えない範囲は、gemma3 が請求情報抽出自体に失敗した、llama3.1 や gemma3 が丁寧な rewrite 自体をできない、gemma3 が rewrite で確実に 2 文出力した、という解釈である。
- さらに、各 prompt が 1 case ずつで run 反復もないため、現状結果から広い意味での安定性能や一般能力差まで主張するのも難しい。

## 推奨条件または推奨指標

- extraction と constrained_generation では、json_valid_rate / format_valid_rate を strict machine-consumable gate として維持するのがよい。
- そのうえで、benchmark の意味を広げたいなら、code fence や前後空白だけを正規化してから parse する tolerant な副指標を別名で追加し、strict gate と混ぜないのがよい。fail を消すためではなく、payload correctness と transport cleanliness を分離するためである。
- rewrite は、現状の prompt と scorer を使うなら「丁寧表現への書き換え」一般ではなく、「exact phrase と 1 文制約を含む strict lexical instruction-following rewrite」と説明するのがよい。
- もし rewrite を自然な丁寧化能力まで含めて見たいなら、exact phrase を要求する prompt と、意味保持・自然さを別軸でみる prompt を分けるのがよい。少なくとも現行 constraint_pass_rate を rewrite quality の代理としては読まない方がよい。
- 結果の可読性のため、required_phrase と sentence_count は将来的に constraint 別に表示できると解釈が安定する。

## 根拠メモ

- prompts/extraction/invoice-fields-v1.toml と prompts/constrained_generation/followup-action-json-v1.toml は、いずれも JSON のみを返す契約を明示している。
- prompts/rewrite/polite-rewrite-v1.toml は、1 文かつ「少々お待ちください」を含め、「待って」を含めない契約を明示している。
- case-evaluations.jsonl では gemma3 invoice-fields-v1 が parse_error により exact_match_rate / json_valid_rate fail、gemma3 と qwen2.5 の followup-action-json-v1 が parse_error により constraint_pass_rate / format_valid_rate fail、llama3.1 の polite-rewrite-v1 が required_phrase fail、gemma3 の polite-rewrite-v1 が required_phrase と sentence_count fail になっている。
- records.jsonl と raw response では、gemma3 invoice-fields-v1 と gemma3 / qwen2.5 followup-action-json-v1 が fenced code block を返している。gemma3 polite-rewrite-v1 は見た目上 1 文である。
- README は extraction の json_valid_rate と constrained_generation の format_valid_rate を運用 gate とし、rewrite を constraint_pass_rate による明示制約遵守として説明している。
- evaluation.py は _parse_json で raw parse のみを行い、_score_constraint_pass は required_phrases の部分一致、sentence_count の句読点ベース判定、required_values の raw JSON parse を使う。

## 未解決事項

- gemma3 の polite-rewrite-v1 で observed_sentence_count = 2 になった理由は、artifact と current code だけでは説明し切れない。run 時点のコード差分、hidden character、または heuristic の edge case を切り分ける再現確認が別途必要である。
- current benchmark には payload correctness と wrapper cleanliness を分離する tolerant metric がない。
- rewrite の自然さ、意味保持、許容言い換えは現行 auto 評価の外側にある。

## 改善提案

- JSON task は、strict contract benchmark と tolerant payload benchmark を分けて設計するのがよい。前者は現行の json_valid_rate / format_valid_rate を維持し、後者は code fence など一般的 wrapper を剥がした後の payload correctness を別 metric で見る。
- extraction は、現行 exact_match_rate の読み方を end-to-end machine-readable exact match と明示するか、tolerant payload exact match を追加して意味を分離するのがよい。
- rewrite は、strict lexical instruction-following prompt と natural polite rewrite prompt を分けるのがよい。現行 prompt を残すなら、exact phrase fail は仕様どおりだが、意味品質の fail ではないことを README や report 上でも明示した方がよい。
- sentence_count は、current artifact の説明可能性が弱いため、独立表示または再現テスト追加の優先度が高い。fail を消すためではなく、constraint の意味と検証可能性を揃えるためである。

# 成果

- project-master が統合しやすいよう、strict contract と tolerant quality の境界、現状結果の許容解釈範囲、見直し方針を整理した。
- 現行 benchmark は「機械可読な JSON をそのまま返せるか」「明示した lexical / structural constraint を守れるか」を測るものとしては妥当である、という結論を残した。
- ただし extraction semantic quality と rewrite quality を広く評価する benchmark として読むのは過剰であり、特に sentence_count は追加確認なしに強く解釈しない方がよい、と明記した。

# 次アクション

- project-master は、本タスクの結論を「strict contract benchmark としては妥当。ただし semantic quality の主張範囲は限定し、strict/tolerant split を次の候補にする」として統合できる。
- 次の request を切るなら、JSON の strict/tolerant 分離と、rewrite の strict lexical prompt / natural rewrite prompt の分離を別タスクに分けるのがよい。