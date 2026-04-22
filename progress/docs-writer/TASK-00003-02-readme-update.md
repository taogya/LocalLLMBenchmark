# TASK-00003-02 README 更新 (新規ドキュメント参照とロードマップ整合)

- Status: review-pending
- Role: docs-writer
- Parent: TASK-00003
- Related IDs: REQ-00001..REQ-00009

## 目的

TASK-00003-01 で追加された 6 件の上位設計ドキュメントを README から辿れるようにし、ロードマップと整合させる。

## 成果物

- `README.md` の「関連ドキュメント」セクションに新規追加分を追記
- 必要に応じてロードマップの v1.0.0 / v0.1.0 表現を新ドキュメント (受入基準) と整合
- 「使い方の概観 (v1)」の保留表現を、CLI surface 文書が確定した上で要点だけ言及するよう微修正 (ただし具体コマンドは実装後に追記する原則を維持)

## 制約

- 設計内容の意味を変えない (リンクと整合のみ)
- `docs/requirements/` `docs/design/` `docs/development/` 配下を編集しない
- 一次情報は TASK-00003-01 の成果物を採用する

## 完了条件

- README に追加リンクが記載されている
- TASK-00003-01 の確定内容と矛盾がない
- `Status: review-pending` に更新

## 着手条件

- TASK-00003-01 が `done` または `review-pending`

## 進捗ログ

- 2026-04-19: README.md を更新。
  - 「関連ドキュメント」に docs/design/05〜08 と docs/development/environment.md, release-criteria.md の 6 件のリンクを追加 (既存の docs/design/04, docs/development/traceability.md の直後に並べた)。
  - 「ロードマップ」v1.0.0 末尾に受入基準の正本が docs/development/release-criteria.md である旨を 1 行追記。
  - 「使い方の概観 (v1)」末尾の保留文を docs/design/05-cli-surface.md と docs/design/06-configuration-sources.md への参照に置換 (具体コマンドは実装後追記の原則は維持)。
- 参照した一次情報: TASK-00003-01 で追加された docs/design/05-cli-surface.md, 06-configuration-sources.md, 07-provider-contract.md, 08-scoring-and-ranking.md, docs/development/environment.md, docs/development/release-criteria.md。
- Status を `review-pending` に更新。
