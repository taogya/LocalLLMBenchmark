---
request_id: "00006"
task_id: "00006-01"
parent_task_id: "00006-00"
owner: "evaluation-analyst"
title: "define-scorers-and-thresholds"
status: "done"
depends_on: []
created_at: "2026-04-18T00:20:00+09:00"
updated_at: "2026-04-18T01:10:00+09:00"
related_paths:
  - "docs/architecture/prompt-and-config-design.md"
  - "prompts"
  - "src/local_llm_benchmark/storage"
---

# 入力要件

- scorer 定義と閾値を先に固めたい。
- ResultSink 実装と合わせて扱えるよう、保存すべき評価条件も明確にしたい。

# 整理した要件

- 初期フェーズで固定する scorer と閾値を、カテゴリごとに短く定義する。
- README で利用者に伝える粒度と、実装が保存すべき粒度の両方を整理する。
- 未確定の項目が残る場合は、それも明示する。

# 作業内容

- docs/architecture/prompt-and-config-design.md に、scorer と集計 metric の分離、初期フェーズで固定する deterministic scorer、カテゴリ別の pass 条件、ResultSink が追跡すべき評価条件を追記した。
- classification の TOML 例を、accuracy と macro_f1 を exact_match_label で集計する形にそろえ、prediction_path と label_space を output_contract で示した。
- 現行 sample prompt が manual_check 寄りであることを前提に、初期フェーズで本当に自動化する範囲と、manual または後続実装へ回す範囲を切り分けた。

# 判断

- 初期フェーズで固定するのは、provider 非依存かつ deterministic に判定できる scorer に限るのが妥当。
- accuracy や macro_f1 は scorer ではなく run 集計 metric なので、ResultSink は metric 名だけでなく、その元になった case scorer と集計方法を保存する必要がある。
- evaluation_metadata.reference_type は primary_metric の参照型としては有効だが、secondary metric が別の reference_type を使うため、ResultSink では metric ごとの evaluation_conditions を持たせる方が実装しやすい。
- rewrite、summarization、short_qa の品質系指標は、現時点では scorer 定義や閾値の較正根拠が弱く、official pass/fail に使うべきではない。
- structured output を downstream に渡す用途では json_valid_rate または format_valid_rate を 1.0 とみなす運用 gate は固定してよいが、accuracy や exact_match_rate の run 閾値は dataset 較正前なので未固定とした。

# 成果

## 評価対象

- 初期フェーズで fixed にした scorer は exact_match_label、exact_match_text、exact_match_json_fields、json_valid、format_valid、constraint_pass、length_compliance とした。
- 6 カテゴリのうち、classification と extraction はすぐ自動評価へ移せる対象、rewrite と summarization と short_qa は部分自動、constrained_generation は output_contract 前提で自動評価できる対象として整理した。

## 推奨条件または推奨指標

- classification は exact_match_label v1 を case scorer とし、accuracy と macro_f1 を run 集計する。case pass は exact_match = 1 とした。
- extraction は exact_match_json_fields v1 と json_valid v1 を使い、exact_match_rate と json_valid_rate を集計する。case pass は json_valid = 1 かつ exact_match = 1 とした。
- rewrite は constraint_pass v1 だけを自動評価で固定し、constraint_pass_rate を使う。similarity は v0 または manual とした。
- summarization は length_compliance v1 だけを固定し、length_compliance_rate を使う。rouge_like は v0 または manual とした。
- short_qa は exact_match_text v1 だけを固定し、exact_match_rate を使う。factuality_check は manual または hybrid とした。
- constrained_generation は constraint_pass v1 と format_valid v1 を固定し、constraint_pass_rate と format_valid_rate を使う。
- ResultSink が保存すべき評価条件は、metric_name、scorer_name、scorer_version、reference_type、aggregation、threshold、pass_rule、metric_definition、expected_output_format、output_contract_snapshot、evaluation_mode とした。

## 根拠メモ

- 00005 で整理した指標候補のうち、exact match、JSON 妥当性、構造妥当性、長さ制約のような deterministic 指標は、provider や judge モデルに依存せず再現性を保ちやすい。
- macro_f1 は label 空間と normalized prediction/reference がないと再計算できないため、ResultSink は評価条件だけでなく scorer の解釈条件も残す必要がある。
- extraction の json_valid_rate、constrained_generation の format_valid_rate は、モデル品質というより運用投入可能性を見る gate として意味がある。

## 未解決事項

- similarity の scorer 定義は、embedding、文字 n-gram、judge など候補が複数あり、日本語 rewrite での較正が未完了。
- rouge_like は日本語 tokenization と参照要約数の前提が未固定であり、しきい値も根拠不足。
- factuality_check は根拠データの持ち方と manual/hybrid/automatic の責務境界が未定。
- 現行 sample prompt の evaluation_metadata は manual_check のままなので、programmer 側で prompt metadata を docs に合わせて更新する必要がある。

## 改善提案

- ResultSink は prompt 単位の evaluation_metadata だけでなく、metric ごとの evaluation_conditions 配列を保存し、secondary metric の reference_type 差分を吸収できる形にする。
- rewrite、summarization、constrained_generation の prompt では output_contract を拡張し、文数、文字数、必須語句、required_keys など machine-readable 制約を明示すると自動評価範囲を広げやすい。
- quality 系 scorer を固定する前に、人手評価付きの小さな calibration set を用意し、similarity、rouge_like、factuality_check の相関を確認する方がよい。

# 次アクション

- solution-architect は metric ごとの evaluation_conditions を前提に ResultSink の保存スキーマを設計する。
- programmer は docs の fixed scorer 定義に合わせて prompt metadata と ResultSink 実装を更新する。
- reviewer は automatic と manual の境界が README、docs、storage 実装で一貫しているかを確認する。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md
- prompts