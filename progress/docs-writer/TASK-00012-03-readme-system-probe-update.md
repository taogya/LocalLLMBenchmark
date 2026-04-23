# TASK-00012-03 README の v1.2.0 / subcommand 記述更新

- Status: done
- Role: docs-writer
- Parent: TASK-00012
- Related IDs: REQ-00001
- 起票日: 2026-04-22

## 目的

`system-probe` の名称と利用者向け説明が確定したら、README の v1.2.0 ロードマップ節とサブコマンド一覧へ反映する。利用者が初回ベンチ前の確認コマンドとして位置づけを理解できる状態にする。

## 完了条件

- 着手時点で TASK-00012-01 が `done`、TASK-00012-02 が少なくとも `review-pending` になっている。
- README の v1.2.0 ロードマップ節に `system-probe` の目的が反映されている。
- README のサブコマンド一覧に `system-probe` が追加され、既存説明と矛盾しない。
- 利用者向け記述にトレース ID や内部実装詳細を露出していない。

## スコープ外

- 設計文書更新 (TASK-00012-01)
- `system-probe` 実装 (TASK-00012-02)
- 最終レビュー (TASK-00012-04)

## 進捗ログ

- 2026-04-22 project-master: 起票。README 更新要件を親 task の完了条件から分離
- 2026-04-23 docs-writer: TASK-00012-01 が `done`、TASK-00012-02 が `review-pending` であることを確認し、README の更新対象を v1.2.0 ロードマップ節とサブコマンド一覧に限定して着手した。
- 2026-04-23 docs-writer: [README.md](README.md) に `system-probe` を追加し、初回ベンチ前に実行環境情報・provider 疎通・候補モデル可用性を 1 コマンドで確認する目的を反映した。利用者向け記述のみに限定し、トレース ID や内部実装詳細は記載していない。
- 2026-04-23 docs-writer: [README.md](README.md) と [progress/docs-writer/TASK-00012-03-readme-system-probe-update.md](progress/docs-writer/TASK-00012-03-readme-system-probe-update.md) に対して診断を実行し、新規エラーがないことを確認した。完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-23 docs-writer: [progress/reviewer/TASK-00012-04-review-system-probe.md](progress/reviewer/TASK-00012-04-review-system-probe.md) で判定が「合格」、Status が `done` であることを確認した。reviewer 合格を受けて本 task を完了とし、Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)
