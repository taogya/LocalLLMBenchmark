---
request_id: "00005"
task_id: "00005-01"
parent_task_id: "00005-00"
owner: "evaluation-analyst"
title: "define-initial-evaluation-metrics"
status: "done"
depends_on: []
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-17T23:45:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
---

# 入力要件

- ルート README に、初期フェーズで使う評価指標と、その指標から何が分かるかを記載する。
- 評価指標が既に決まっているかどうかも明確にする。

# 整理した要件

- 既存 docs にある候補をベースに、README に載せる初期方針を短く整理する。
- 指標名の列挙だけでなく、利用者視点での読み解きを添える。
- まだ最終固定でないなら、その前提も README に書く。

# 作業内容

- README に初期評価指標セクションを追加し、カテゴリごとの主要指標と「何が分かるか」を 1 行で整理した。
- README に、この指標群が最終固定ではなく現時点の初期方針であることと、指標の読み解き例を追記した。
- docs/architecture/prompt-and-config-design.md のカテゴリ別候補と照合し、README の表現を既存 docs の範囲に収めた。

# 判断

- 「評価指標は既に決まっていたのか」への回答は、「docs では候補が整理済みだが README には未反映で、最終固定版ではない」が妥当。
- README では scorer 実装や保存スキーマの細部まで踏み込まず、利用者がモデル差を読むための最小説明に留めた方が短く実用的。
- sample prompt に未同梱のカテゴリもあるため、「初期フェーズで想定する比較方針」として書くのが現状と整合する。

# 成果

## 評価対象

- 初期フェーズで想定するカテゴリは classification、extraction、rewrite、summarization、short_qa、constrained_generation とした。

## 推奨条件または推奨指標

- classification: accuracy、macro_f1
- extraction: exact_match、json_valid_rate
- rewrite: constraint_pass_rate、similarity
- summarization: rouge_like、length_compliance
- short_qa: exact_match、factuality_check
- constrained_generation: constraint_pass_rate、format_valid_rate

## 根拠メモ

- docs/architecture/prompt-and-config-design.md にカテゴリ別の主な評価軸候補があり、README はその利用者向け要約として位置づけるのが自然。
- 初期フェーズでは、正答性を見る指標と、形式や制約を守れるかを見る指標を組み合わせるとモデル差を説明しやすい。

## 未解決事項

- factuality_check、similarity、rouge_like の scorer 定義と閾値は、結果保存設計とあわせて今後固定する必要がある。
- カテゴリごとの sample prompt と評価データのカバレッジは今後の整備対象であり、README だけでは実装完了を意味しない。

## 改善提案

- ResultSink 実装時に metric_definition、scorer_version、reference_type を保存し、将来の比較条件差分を追跡しやすくする。
- README とは別に docs/architecture 側へ scorer 定義表を追加すると、実装時の解釈ぶれを減らせる。

# 次アクション

- reviewer へ README と docs の整合性確認を引き継ぐ。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md