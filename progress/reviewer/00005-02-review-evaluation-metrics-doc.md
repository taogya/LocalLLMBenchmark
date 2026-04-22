---
request_id: "00005"
task_id: "00005-02"
parent_task_id: "00005-00"
owner: "reviewer"
title: "review-evaluation-metrics-doc"
status: "done"
depends_on:
  - "00005-01"
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-17T21:58:51+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
---

# 入力要件

- README に追加された評価指標の説明を最終確認する。

# 整理した要件

- README が短く実用的であること。
- 「何を評価するか」と「その指標から何が分かるか」が読み手に伝わること。
- 「既に決まっていたのか」への答えとして、確定事項と未確定事項の線引きが適切であること。
- 既存 docs との整合が取れていること。

# 作業内容

- README の初期評価指標セクションを読み、カテゴリ、主指標、読み解き例、未確定の書き方を確認した。
- docs/architecture/prompt-and-config-design.md の初期カテゴリ案と評価軸を照合し、6 カテゴリと指標名が一致していることを確認した。
- README の読み解き例に `constrained_generation` と `similarity` を同時に並べる軽微な不整合があったため、表の定義に合わせて最小修正した。

# 判断

- README は表と短い補足だけで構成されており、ルート文書として過不足のない長さに収まっている。
- 「当面は 6 カテゴリと主指標を比較軸として扱う」と「最終固定版ではない」を併記したため、現時点で使う前提と未確定部分の線引きは適切である。
- docs/architecture/prompt-and-config-design.md にある初期カテゴリ案と評価軸の説明と矛盾はない。
- 未解消の重大 finding はない。

# 成果

- 確認対象:
  - README.md
  - docs/architecture/prompt-and-config-design.md
  - progress/reviewer/00005-02-review-evaluation-metrics-doc.md
- 発見事項:
  - 解消済みの軽微事項: README の読み解き例で `constrained_generation` に `similarity` を並記しており、表とずれていたため、README を最小修正した。
  - 未解消の重大 finding はなし。
- 残課題:
  - `factuality_check`、`similarity`、`rouge_like` の scorer 定義と閾値は今後の結果保存設計とあわせて固定が必要。
  - `summarization`、`short_qa`、`constrained_generation` は現行 sample prompt に未同梱であり、README は初期方針の説明までに留まる。
- ユーザー報告可否:
  - 可能。README は短く実用的で、評価対象と読み解き方、未確定事項の扱いが現状粒度で伝わる。
- 改善提案:
  - ResultSink 実装時に metric_definition、scorer_version、reference_type を保存できるようにすると、初期方針から固定版へ移る際の比較条件差分を追跡しやすい。

# 次アクション

- project-master へ確認結果を引き継ぐ。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md