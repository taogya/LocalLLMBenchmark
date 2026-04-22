---
request_id: "00009"
task_id: "00009-02"
parent_task_id: "00009-00"
owner: "prompt-analyst"
title: "design-missing-sample-prompts"
status: "done"
depends_on:
  - "00009-01"
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T15:10:00+09:00"
related_paths:
  - "docs/architecture/prompt-and-config-design.md"
  - "prompts/classification/contact-routing-v1.toml"
  - "prompts/extraction/invoice-fields-v1.toml"
  - "prompts/rewrite/polite-rewrite-v1.toml"
  - "configs/prompt_sets/core-small-model-ja-v1.toml"
---

# 入力要件

- summarization / short_qa / constrained_generation の sample prompt と evaluation_reference の最小セットを設計する。
- 6 カテゴリ各 1 prompt をそろえる前提で、core-small-model-ja-v1 への含め方も決める。
- deterministic scorer だけで成立する machine-readable 条件に寄せる。

# 整理した要件

- provider 依存情報を入れず、小型ローカルモデル比較向けに短く分かりやすい prompt にする。
- output_contract は fixed deterministic scorer が使う条件に合わせ、過剰な quality 要件は持ち込まない。
- metadata.evaluation_reference は全 prompt でセクションを持たせ、reference_type ごとに最小 shape をそろえる。

# 作業内容

- docs/architecture/prompt-and-config-design.md、既存 3 prompt、core-small-model-ja-v1、request 00009 の親タスクと evaluation-analyst の整理結果を確認した。
- 既存 prompt の shape を前提に、新規 3 カテゴリの prompt_id、title、description、user_message の方向性を設計した。
- deterministic scorer と整合する output_contract と metadata.evaluation_reference の最小 shape を決めた。
- core-small-model-ja-v1 は explicit な prompt_ids を維持して 6 件へ拡張する方針とし、既存 3 prompt の追加整合有無を確認した。

# 判断

- core-small-model-ja-v1 は include_categories へ切り替えず、explicit な prompt_ids を維持する方がよい。sample corpus が将来の prompt 追加で暗黙に変わらず、比較条件を固定しやすいためである。
- metadata.evaluation_reference の naming は wrapper 名を増やさず、classification は label、short_qa は text、extraction は既存どおり field 直下の object でそろえる方が実装が単純である。
- reference_type = none の prompt でも [metadata.evaluation_reference] の空 table を持たせる方が、6 prompt の shape と review 観点がそろう。
- summarization は fixed scorer が length_compliance v1 のみなので、output_contract は type = "text" と length_range に留める。
- constrained_generation は JSON を採用するのが最小構成として妥当である。expected_output_format = "json" と required_keys の組み合わせが format_valid の運用 gate を最も明確にできる。

# 成果

## プロンプトの目的

- summarization: 短い本文から、指定した文字数レンジに収まる要約を返せるかを比較する。
- short_qa: 短い文脈から、単一の正答文字列を余計な文言なしで返せるかを比較する。
- constrained_generation: 必須キーを持つ JSON と必須語句の両方を守れるかを比較する。

## 推奨レコード

### 1. meeting-notice-summary-v1

- prompt_id: meeting-notice-summary-v1
- category: summarization
- title: 会議案内要約
- description: task_id 00009-04: 初期比較用の短い summarization prompt。
- user_message の方向性:
  - 社内連絡の短文を 1 件だけ置き、会議時刻変更、資料提出期限、欠席連絡期限のような 3 事実を含める。
  - 指示は「80〜120 文字で要約」「出力は本文のみ」に留める。
  - scorer が意味妥当性までは見ないため、要件は長さ制約中心に寄せる。
- 推奨 user_message 例:

```text
次の連絡文を 80〜120 文字で要約してください。
出力は本文のみを返してください。

原文:
来週水曜の顧客説明会は 14 時開始に変更します。発表資料は前日 17 時までに共有フォルダへ入れてください。会場参加が難しい場合は火曜正午までに担当へ連絡してください。
```

- evaluation_metadata:

```toml
[evaluation_metadata]
primary_metric = "length_compliance_rate"
reference_type = "none"
scorer = "length_compliance"
difficulty = "starter"
language = "ja"
expected_output_format = "text"
```

- output_contract:

```toml
[output_contract]
type = "text"

[output_contract.length_range]
min_chars = 80
max_chars = 120
unit = "chars"
```

- metadata.evaluation_reference:

```toml
[metadata.evaluation_reference]
```

### 2. support-hours-answer-v1

- prompt_id: support-hours-answer-v1
- category: short_qa
- title: 受付時間の短答
- description: task_id 00009-04: 初期比較用の短い short_qa prompt。
- user_message の方向性:
  - 1 文脈と 1 問だけの短い QA にする。
  - 出力形式は「17:00 のように時刻だけ」のように exact match しやすい形で明示する。
  - 一意な答えになる文脈を使い、敬語や説明文を要求しない。
- 推奨 user_message 例:

```text
文脈:
サポート窓口の受付時間は平日 9:00 から 17:00 までです。

質問:
受付終了時刻は何時ですか。

回答は 17:00 のように時刻だけを返してください。
```

- evaluation_metadata:

```toml
[evaluation_metadata]
primary_metric = "exact_match_rate"
reference_type = "text"
scorer = "exact_match_text"
difficulty = "starter"
language = "ja"
expected_output_format = "text"
```

- output_contract:

```toml
[output_contract]
type = "text"
```

- metadata.evaluation_reference:

```toml
[metadata.evaluation_reference]
text = "17:00"
```

### 3. followup-action-json-v1

- prompt_id: followup-action-json-v1
- category: constrained_generation
- title: 制約付き JSON 生成
- description: task_id 00009-04: 初期比較用の短い constrained_generation prompt。
- user_message の方向性:
  - 1 件の短いメモを JSON に整形させる。
  - キー数を固定し、priority の固定値と action の必須語句を明示する。
  - format_valid と constraint_pass の両方が効くよう、出力は JSON のみと指示する。
- 推奨 user_message 例:

```text
次のメモを JSON で整理してください。
条件:
- キーは "channel", "priority", "action" の 3 つだけにしてください。
- priority の値は "high" にしてください。
- action には「折り返し」を含めてください。
- 出力は JSON のみを返してください。

メモ:
顧客にはメールで連絡し、至急のため本日中に折り返し対応します。
```

- evaluation_metadata:

```toml
[evaluation_metadata]
primary_metric = "constraint_pass_rate"
secondary_metrics = ["format_valid_rate"]
reference_type = "none"
scorer = "constraint_pass"
difficulty = "starter"
language = "ja"
expected_output_format = "json"
```

- output_contract:

```toml
[output_contract]
type = "json_object"
constraint_ids = [
  "required_keys",
  "include_mail_phrase",
  "include_priority_high",
  "include_callback_phrase",
]
required_keys = ["channel", "priority", "action"]
required_phrases = ["メール", "high", "折り返し"]

[output_contract.field_types]
channel = "string"
priority = "string"
action = "string"
```

- metadata.evaluation_reference:

```toml
[metadata.evaluation_reference]
```

## metadata.evaluation_reference の shape

- classification: [metadata.evaluation_reference] label = "..."
- extraction: [metadata.evaluation_reference] の直下に required_fields と同名の key をそのまま置く。既存の invoice-fields-v1 の shape を維持する。
- short_qa: [metadata.evaluation_reference] text = "..."
- rewrite / summarization / constrained_generation: [metadata.evaluation_reference] の空 table を置く。

## core-small-model-ja-v1 への含め方

- prompt_set の解決方式は現状どおり explicit な prompt_ids のままでよい。
- 並び順はカテゴリの読みやすさを優先して、既存 3 件の後ろに新規 3 件を足すのが最小差分である。
- 推奨更新形は次のとおり。

```toml
prompt_set_id = "core-small-model-ja-v1"
description = "task_id 00004-02: 小型ローカルモデルの初期比較に使う prompt set。"
prompt_ids = [
  "contact-routing-v1",
  "invoice-fields-v1",
  "polite-rewrite-v1",
  "meeting-notice-summary-v1",
  "support-hours-answer-v1",
  "followup-action-json-v1",
]
```

## 既存 3 prompt への整合修正有無

- contact-routing-v1: 修正不要。label reference と output_contract の shape は今回の方針と整合している。
- invoice-fields-v1: 修正不要。json reference を field 直下へ持つ shape をそのまま基準にしてよい。
- polite-rewrite-v1: [metadata.evaluation_reference] の空 table だけ追加した方がよい。reference_type = none の prompt でも evaluation_reference セクションをそろえる方が request 00009 の acceptance とレビュー観点に合う。

## リスクや注意点

- summarization は deterministic では length_compliance しか見ないため、意味妥当性は今回の scope 外である。user_message に未評価の quality 要件を増やしすぎない方がよい。
- short_qa は exact match が厳しいため、答えの表記ゆれが起きない指示にする必要がある。時刻、番号、単語 1 つのような短い答えを選ぶべきである。
- constrained_generation は bullet_list より JSON の方が format_valid の判定基準を固定しやすい。

## 改善提案

- programmer は prompts/summarization、prompts/short_qa、prompts/constrained_generation 配下へ 1 件ずつ追加し、各 prompt に空または最小の metadata.evaluation_reference を明示した方がよい。
- tests では新規 3 prompt の metadata と output_contract が expected_output_format と矛盾しないことを固定し、rewrite の空 evaluation_reference も合わせて検証すると崩れにくい。
- short_qa の reference key は text へ統一し、expected_text のような別名は増やさない方が、classification の label と extraction の field 直下 shape と並べて理解しやすい。

# 次アクション

- programmer は新規 3 prompt を追加し、polite-rewrite-v1 に空の metadata.evaluation_reference を加える。
- programmer は configs/prompt_sets/core-small-model-ja-v1.toml を 6 prompt_id 構成へ更新する。
- reviewer は 6 prompt の evaluation_metadata、output_contract、metadata.evaluation_reference が deterministic scorer 前提と一致しているかを確認する。

# 関連パス

- docs/architecture/prompt-and-config-design.md
- prompts/classification/contact-routing-v1.toml
- prompts/extraction/invoice-fields-v1.toml
- prompts/rewrite/polite-rewrite-v1.toml
- configs/prompt_sets/core-small-model-ja-v1.toml