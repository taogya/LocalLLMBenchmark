# トレーサビリティ (Traceability)

設計と実装、進行管理を ID で連結し、変更影響を辿れるようにします。

## ID 体系

すべての ID は **カテゴリ prefix + ハイフン + 5 桁 0 埋め連番** で構成します。連番は同一カテゴリ内で単調増加とし、欠番は再利用しません。

| Prefix | 対象 | 主管 | 出典文書 |
| --- | --- | --- | --- |
| REQ- | 要求 | solution-architect | docs/requirements/01-overview.md |
| FUN- | 機能要件 | solution-architect | docs/requirements/02-functional.md |
| NFR- | 非機能要件 | solution-architect | docs/requirements/03-non-functional.md |
| OOS- | 非対象 | solution-architect | docs/requirements/04-out-of-scope.md |
| ARCH- | アーキテクチャ判断 | solution-architect | docs/design/01-architecture.md |
| COMP- | コンポーネント | solution-architect | docs/design/02-components.md |
| DAT- | 概念データモデル | solution-architect | docs/design/03-data-model.md |
| FLW- | 主要フロー | solution-architect | docs/design/04-workflows.md |
| CLI- | CLI 表面 (サブコマンド・終了コード方針) | solution-architect | docs/design/05-cli-surface.md |
| CFG- | 設定ソース (ファイル種別・認証情報の取り扱い) | solution-architect | docs/design/06-configuration-sources.md |
| PVD- | Provider 契約 (推論 I/O・失敗種別) | solution-architect | docs/design/07-provider-contract.md |
| SCR- | 採点 scorer 語彙とランキング算出規則 | solution-architect | docs/design/08-scoring-and-ranking.md |
| ROLE- | カスタムエージェントのロール | project-master | docs/development/roles.md |
| PROG- | 進行管理上のリスク | project-master | docs/development/progress.md |
| TASK- | 進行管理上の作業単位 | project-master (親) / 各ロール (子) | progress/ |

実装時に新規カテゴリが必要な場合 (例: `IMPL-` `TEST-`) は、本書に追記してから採番を開始します。

## 採番規約

| ID | 規約 |
| --- | --- |
| TRC-00001 | 連番は同一カテゴリ内で 1 から開始する |
| TRC-00002 | 一度発行した ID は意味を変更しない。意味が変わる場合は新 ID を採番し、旧 ID を `superseded by NEW-ID` と本文に記す |
| TRC-00003 | ID の削除は禁止する。廃止する場合は本文に `Status: deprecated` を併記する |
| TRC-00004 | 採番台帳を別途持たない。出典文書本体を一次情報とする |

### supersede 運用の例

意味が変わる ID を発見した場合は、新 ID を同一カテゴリの末尾に採番し、旧 ID 行はそのまま残す。例:

- `FUN-00201` (複数 Model 指定の Run) → `FUN-00207` (1 Run = 1 Model) を新規採番。`FUN-00201` の本文には `(superseded by FUN-00207)` を併記し、内容自体は履歴として残す。
- `COMP-00003 Run Coordinator` の責務が変わるため `COMP-00010` を新規採番し、`COMP-00003` 側に `(superseded by COMP-00010)` を併記する。

supersede の対応関係は、改訂を行った task の進捗ログに「旧 ID → 新 ID」の対応表を残す。

## 連結ルール

| ID | ルール |
| --- | --- |
| TRC-00101 | FUN- / NFR- は対応する REQ- を本文で参照する (該当する場合) |
| TRC-00102 | ARCH- / COMP- / DAT- / FLW- は根拠となる FUN- / NFR- を本文で参照する |
| TRC-00103 | TASK- は本文の冒頭で対象 ID 群を列挙する。実装系 task は対応する COMP- 以上の粒度を必ず含む |
| TRC-00104 | 実装ファイルにはコメントヘッダで対応 TASK- を 1 つ以上記す。複数 task で改修した行はすべての TASK- を併記する |

## 影響分析の標準手順

設計または実装を変更する前に、次の手順で影響範囲を確定してから着手します。

1. 変更対象の ID を特定する。
2. 同一文書内で該当 ID を参照している箇所を洗い出す。
3. 他文書 (`docs/` 配下) で該当 ID を参照している箇所を洗い出す。
4. progress 配下の TASK- 本文で該当 ID を参照している箇所を洗い出す。
5. 影響範囲を親 task の本文に記録した上で着手する。

## 例: 機能追加時の連結

```
REQ-00009 (新用途追加)
  └─ FUN-00102 (Case 追加)
        ├─ COMP-00008 Task Catalog
        │     └─ DAT-00002 Case
        └─ FLW-00003 (整合性確認)
              └─ TASK-00012 (実装)
                    └─ TASK-00012-01 (programmer)
                    └─ TASK-00012-02 (reviewer)
```

新規 ID を増やすたびに、上記のような縦の連結が形成されることを確認します。

## ID の見え方

- ドキュメント本文では ID をそのまま埋め込む。
- 表形式では先頭列を `ID` とする。
- コメント・コミットメッセージでは `TASK-NNNNN-SS:` を文頭に置く。
