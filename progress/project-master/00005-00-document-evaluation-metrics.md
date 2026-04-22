---
request_id: "00005"
task_id: "00005-00"
parent_task_id:
owner: "project-master"
title: "document-evaluation-metrics"
status: "done"
depends_on: []
child_task_ids:
  - "00005-01"
  - "00005-02"
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-18T00:05:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
---

# 入力要件

- 結果保存の前に、何を評価するかをルート README に記載したい。
- ユーザーとしては、評価指標と、その指標から何が分かるかが重要である。
- 評価指標が既に決まっているかも明確にしたい。

# 整理した要件

- README には、初期フェーズで採用する評価指標の候補と意味を、初心者でも読める短さで整理する。
- 既存 docs にある候補指標は活かすが、まだ最終固定ではない場合はその前提を明示する。
- project-master は progress 管理と委譲を担当し、評価指標の整理と README 更新は評価アナリストへ委譲する。

# 作業内容

- 既存 README と architecture docs を確認し、評価指標はカテゴリ別の候補まであり、README 反映と初期方針の明文化は未完了であることを確認した。
- 評価アナリスト向け子タスクとレビュアー向け子タスクを作成し、README 反映まで進める準備を整えた。
- 評価アナリストが、README に初期評価指標セクションを追加し、6 カテゴリの主指標と「何が分かるか」を利用者向けに整理した。
- レビュアーが README と architecture docs の整合性を確認し、軽微な読み解き例のずれを最小修正したうえで、重大 finding なしと判断した。

# 判断

- 指標の最終固定まではまだ進んでいないため、README には「現時点の初期方針」として書くのが妥当。
- 何が分かるかを併記しないと README として弱いため、指標名だけでなく読み解きも必須とする。

# 成果

- request_id 00005 の親記録を作成した。
- README に、classification、extraction、rewrite、summarization、short_qa、constrained_generation の 6 カテゴリについて、初期評価指標と読み解き方を追加した。
- 「評価指標は docs 上では候補整理済みだったが、README に載る形では未確定だった」という前提を、README 上で「現時点の初期方針」「最終固定版ではない」として明示した。
- 既存 docs と矛盾しないこと、README が短く実用的であること、重大 finding がないことを確認した。

# 次アクション

- 次段階では ResultSink 実装とあわせて、metric_definition、scorer_version、reference_type など評価条件の保存単位を固定する。
- `factuality_check`、`similarity`、`rouge_like` の scorer 定義と閾値は、評価データ整備の段階で具体化する。
- `summarization`、`short_qa`、`constrained_generation` は sample prompt 未同梱のため、今後の prompt corpus 整備で実データを追加する。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md