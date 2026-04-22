---
request_id: "00002"
task_id: "00002-01"
parent_task_id: "00002-00"
owner: "solution-architect"
title: "readme-roadmap"
status: "done"
depends_on: []
created_at: "2026-04-17T21:10:00+09:00"
updated_at: "2026-04-17T21:40:00+09:00"
related_paths:
  - "README.md"
  - "docs/ollama"
  - "docs/architecture"
---

# 入力要件

- 実施済みの Ollama 疎通確認結果を踏まえ、次ステップのロードマップを README 末尾へ追加する。
- ロードマップは短く、実務的で、現行アーキテクチャと矛盾しない内容にする。

# 整理した要件

- 現在地を 1 段落で示したうえで、次の段階を優先順で提示する。
- provider 非依存方針を維持し、Ollama 固定の進め方にしない。
- README の説明は初心者でも追いやすい短さに保つ。

# 作業内容

- docs/architecture の責務境界と project-master の親記録を確認し、README へ載せる粒度を絞った。
- README 末尾に、現在地と優先順付きのロードマップを追加した。

# 判断

- 直近の到達点は実 API と最小 benchmark 経路の確認まで進んでいるため、次段階は実行条件をコード外へ出す config 外部化を最優先にした。
- 保存、評価データ、provider 拡張、比較レポートの順に進めることで、provider 非依存の benchmark core を保ったまま比較可能性を段階的に上げられると判断した。
- README は初心者向けに短く保つ必要があるため、詳細設計ではなく、各段階の目的が一読で分かる 5 項目に限定した。

# 成果

- README.md の末尾に、日本語の簡潔なロードマップを追加した。
- 現在地として、Ollama の導入と API、CLI、benchmark 経路の最小疎通確認まで完了していることを明記した。
- 次の優先順位として、config 外部化、結果保存、評価データ整備、provider 拡張、比較レポート整備を README に反映した。

# 次アクション

- project-master が親記録へ結果を統合し、必要なら programmer 側で config 外部化と ResultSink 実装へ着手する。
- 評価アナリストまたは prompt-analyst が、比較に使う prompt corpus と評価メタデータの初期セットを具体化する。

# 関連パス

- README.md
- docs/ollama
- docs/architecture