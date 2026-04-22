---
request_id: "00014"
task_id: "00014-02"
parent_task_id: "00014-00"
owner: "prompt-analyst"
title: "review-json-and-required-phrase-contracts"
status: "done"
depends_on: []
created_at: "2026-04-18T22:00:00+09:00"
updated_at: "2026-04-18T23:05:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "prompts/rewrite/polite-rewrite-v1.toml"
  - "prompts/constrained_generation/followup-action-json-v1.toml"
  - "prompts/extraction/invoice-fields-v1.toml"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tmp/runtime-checks/request-00013-20260418-151043/case-evaluations.jsonl"
  - "tmp/runtime-checks/request-00013-20260418-151043/records.jsonl"
---

# 入力要件

- JSON 出力条件と required phrase 条件が prompt 契約として妥当かを確認したい。
- fail を減らす目的ではなく、strict instruction-following を測る prompt として自然か、改善するならどう分けるべきかを整理したい。
- README の現行評価説明と、runtime artifact の fail 内容が整合しているかも確認する。

# 整理した要件

- prompt 契約は、user_message の自然言語指示だけでなく、evaluation_metadata と output_contract の機械可読な shape まで含めて判断する。
- strict instruction-following と tolerant quality を同じ metric に混ぜず、初期 benchmark の deterministic auto 評価として何を保証したいかを切り分ける。
- 今回は実装ではなく、現行 fail を benchmark として妥当と言える範囲と、次にどこを直すべきかの優先度を明確にする。

# 作業内容

- prompts/rewrite/polite-rewrite-v1.toml、prompts/constrained_generation/followup-action-json-v1.toml、prompts/extraction/invoice-fields-v1.toml、README.md、docs/architecture/prompt-and-config-design.md を確認した。
- tmp/runtime-checks/request-00013-20260418-151043/records.jsonl と case-evaluations.jsonl を確認し、実際の fail が code fence 由来か、required phrase 由来かを切り分けた。
- src/local_llm_benchmark/benchmark/evaluation.py を確認し、json_valid / format_valid / constraint_pass の実判定が raw response に対する json.loads と、required_phrases / forbidden_phrases / sentence_count / required_values の deterministic 判定であることを確認した。
- 観測事実として、invoice-fields-v1 は gemma3 が code fence 付き JSON を返して json_valid と exact_match が fail、followup-action-json-v1 は gemma3 と qwen2.5 が code fence 付き JSON を返して format_valid と constraint_pass が fail、polite-rewrite-v1 は qwen2.5 だけが exact phrase を満たし、gemma3 と llama3.1 は意味的に妥当な丁寧文でも fail していた。

# 確認ポイント

- JSON-only 指示が code fence 付き出力を落とす前提として十分明確か。
- 「少々お待ちください」を exact phrase で要求する設計が、初期 benchmark の目的に合っているか。
- 条件を緩めるのではなく、strict / tolerant の 2 系統に分けるべきか。

# 判断

## 1. JSON-only と code fence fail の妥当性

- 現行の human-facing prompt としては、invoice-fields-v1 の「JSON で {...} のみを返してください」と followup-action-json-v1 の「出力は JSON のみを返してください」は、code fence や前置き文を付けない raw JSON を要求する表現として十分に読める。したがって、現行 run で fenced JSON を fail として扱うこと自体は、strict instruction-following benchmark として妥当である。
- 一方で、structured contract としては `expected_output_format = "json"` と `output_contract.type = "json_object"` だけでは「レスポンス全体が raw JSON でなければ fail」という方針が明文化されていない。現在の厳しさは、README の parse 成功説明と evaluation.py の raw json.loads 実装に依存しており、prompt artifact 単体ではやや暗黙である。
- 結論として、現行 fail 判定は有効だが、prompt 契約として完全に自己記述的とは言い切れない。strict JSON-only を benchmark 契約として維持するなら、prompt 文面か output_contract、少なくとも README / docs 側で「Markdown code fence や説明文付きは fail」と明示した方がよい。

## 2. rewrite の exact required phrase の妥当性

- polite-rewrite-v1 の current scorer が見ているのは、実質的には「丁寧な言い換え品質」ではなく、「指定句をそのまま入れる lexical constraint follow」である。qwen2.5 は pass したが、gemma3 の「少々お時間を頂戴できますでしょうか」と llama3.1 の「しばらくお待ちください」は、自然さや意味の近さがあっても exact phrase 不一致で fail した。
- そのため、この prompt を初期 benchmark の rewrite 代表として置くのは適切ではない。タイトルとカテゴリから受ける期待は「丁寧で自然な rewrite」だが、実測しているのは 1 つの定型句の再現性に近い。
- ただし、strict instruction-following のサンプルとしては不適切ではない。exact phrase を残すなら、「丁寧表現への書き換え」よりも「制約付き rewrite」や「lexical instruction-following」を測る prompt として位置付け直すべきである。

## 3. strict と tolerant を分けるべきか

- 条件をそのまま緩めるより、strict instruction-following と tolerant quality を分ける方がよい。両者は benchmark で答えたい問いが異なるためである。
- strict 側は、raw JSON-only、required_keys、required_values、exact required phrase のような downstream gate に直結する条件を deterministic pass/fail で見る。ここでは fenced JSON や exact phrase 不一致は fail のままでよい。
- tolerant 側は、wrapper を外せば使える JSON か、意味保持と丁寧さは満たしているか、といった実用寄り品質を別 metric で見る。strict fail を tolerant pass で上書きせず、別軸として併記する方が解釈しやすい。
- 特に rewrite は strict と tolerant の混線が大きい。現行の polite-rewrite-v1 は strict 側に寄せ、tolerant 側は別 prompt か manual / hybrid scorer 前提で切り出すのが自然である。

## 4. 次に手を入れる優先度

- 先に手を入れるべきなのは prompt 側とドキュメント側であり、scorer の意味をその場で変えることではない。現行 scorer は strict 契約として一貫しており、まず契約の見え方を揃える方が先である。
- prompt 側では、JSON-only prompt に「Markdown の code fence や補足文を付けず、先頭から末尾まで単一の JSON object だけを返す」といった wording を足すか、strict JSON-only であることが分かる命名やタグを付ける方がよい。rewrite 側では exact phrase 型の prompt を strict rewrite と明示するか、別の tolerant rewrite prompt を追加する方がよい。
- ドキュメント側では、README と docs/architecture/prompt-and-config-design.md に、json_valid / format_valid は raw response 全体の parse 成功を見ること、fenced JSON は strict 契約では fail であること、rewrite の constraint_pass は lexical constraint follow であり自然さや意味保持そのものは見ていないことを明記した方がよい。
- scorer 側は、その後に別 metric を足す形で触るのがよい。strict scorer の既定挙動は維持しつつ、必要なら fenced JSON を救済する tolerant diagnostic scorer、または rewrite の意味保持・丁寧さを見る manual / hybrid scorer を追加するのが筋である。

# 成果

- JSON-only prompt で fenced JSON を fail とする現行判定は、strict instruction-following benchmark として妥当である。
- ただし strictness が prompt artifact の structured contract に十分に露出していないため、prompt wording か docs で補強した方がよい。
- polite-rewrite-v1 の exact phrase 要求は、一般的な rewrite quality の代表としては brittle だが、strict lexical constraint follow のサンプルとしては成立する。
- 今後は条件緩和ではなく、strict instruction-following と tolerant quality を別 prompt / 別 metric として分離する方針が妥当である。
- 次の改善優先度は、1) prompt 契約の明確化、2) README / docs の評価説明の明確化、3) strict を変えずに tolerant scorer を追加、の順である。

# 次アクション

- project-master は evaluation-analyst の fail 妥当性整理と合わせ、現行結果を「strict instruction-following の観点では妥当」と統合してよい。
- strict / tolerant を本当に運用へ入れる場合は、次 request で prompt taxonomy と metric taxonomy を分けて起票するのがよい。