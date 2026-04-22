---
description: "新しい ID (REQ-, FUN-, ARCH- など) を採番・参照するときに使う。ID 体系の運用ルール。"
name: "トレーサビリティ運用ルール"
applyTo: "docs/**/*.md, progress/**/*.md, src/**, tests/**"
---

# トレーサビリティ運用ルール

正本は [docs/development/traceability.md](../../docs/development/traceability.md) です。本書は実務上の最小ルールに絞ります。

## ID 形式

- すべての ID は `<カテゴリ>-NNNNN` (5 桁 0 埋め)
- 採番は同一カテゴリ内で単調増加。欠番は再利用しない
- 一度発行した ID の意味を変更しない。意味を変える場合は新 ID を採番し旧 ID は `superseded by NEW-ID` と本文に併記
- supersede 元と先の対応は改訂を行った task の進捗ログに必ず列挙する

## カテゴリ一覧

| Prefix | 対象 | 主管 |
| --- | --- | --- |
| REQ- | 要求 | solution-architect |
| FUN- | 機能要件 | solution-architect |
| NFR- | 非機能要件 | solution-architect |
| OOS- | 非対象 | solution-architect |
| ARCH- | アーキテクチャ判断 | solution-architect |
| COMP- | コンポーネント | solution-architect |
| DAT- | 概念データモデル | solution-architect |
| FLW- | 主要フロー | solution-architect |
| CLI- | CLI 表面 | solution-architect |
| CFG- | 設定ソース | solution-architect |
| PVD- | Provider 契約 | solution-architect |
| SCR- | 採点・ランキング | solution-architect |
| ROLE- | カスタムエージェントのロール | project-master |
| PROG- | 進行管理上のリスク | project-master |
| TRC- | トレーサビリティ規約 | project-master |
| TASK- | 進行管理上の作業単位 | project-master (親) / 各ロール (子) |

新カテゴリが必要な場合は [docs/development/traceability.md](../../docs/development/traceability.md) に追記してから採番する。

## 連結

- FUN-, NFR- は対応する REQ- を本文で参照する (該当する場合)
- ARCH-, COMP-, DAT-, FLW- は根拠となる FUN-, NFR- を本文で参照する
- TASK- は冒頭の `Related IDs:` で対象 ID 群を列挙する
- 実装ファイルにはコメントヘッダで対応 TASK- を 1 つ以上記す

## 影響分析

設計または実装を変更する前に、対象 ID を起点として `docs/` と `progress/` 配下の参照を洗い出し、影響範囲を親 task に記録した上で着手する。
