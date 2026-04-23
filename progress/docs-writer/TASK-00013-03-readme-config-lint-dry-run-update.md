# TASK-00013-03 README の v1.2.0 / subcommand 記述更新

- Status: done
- Role: docs-writer
- Parent: TASK-00013
- Related IDs: REQ-00001
- 起票日: 2026-04-23

## 目的

`config lint` / `config dry-run` の名称と利用者向け説明が確定したら、README の v1.2.0 ロードマップ節とサブコマンド一覧へ反映する。利用者が「静的検証」と「実行前 preflight」の使い分けを理解できる状態にする。

## 完了条件

- 着手時点で TASK-00013-01 が `done`、TASK-00013-02 が少なくとも `review-pending` になっている。
- README の v1.2.0 ロードマップ節に最終 public surface と役割が反映されている。
- README のサブコマンド一覧に最終 public surface が追加または整理され、既存説明と矛盾しない。
- 利用者向け記述にトレース ID や内部実装詳細を露出していない。

## スコープ外

- 設計文書更新 (TASK-00013-01)
- `config lint` / `config dry-run` 実装 (TASK-00013-02)
- 最終レビュー (TASK-00013-04)

## 進捗ログ

- 2026-04-23 project-master: 起票。README 更新要件を親 task の完了条件から分離
- 2026-04-23 docs-writer: Status を `in-progress` 相当で着手。 [README.md](README.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md](progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md), [progress/programmer/TASK-00013-02-implement-config-lint-dry-run.md](progress/programmer/TASK-00013-02-implement-config-lint-dry-run.md) を確認し、TASK-00013-01 が `done`、TASK-00013-02 が `review-pending` であること、利用者向け主導線が `system-probe` -> `config lint` -> `config dry-run` -> `run` であること、`check` は既存互換面として残ること、`config lint` は単一ファイル / config-dir 両対応の静的確認であること、`config dry-run` は `run` 実行前 preflight であることを確認した。
- 2026-04-23 docs-writer: README のサブコマンド一覧に `config lint` / `config dry-run` と使い分けの短い説明を追加し、v1.2.0 ロードマップ節を同じ公開 surface にそろえた。利用者向け説明に内部実装詳細やトレース ID を出していないことを見直し、完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-23 docs-writer: [progress/reviewer/TASK-00013-04-review-config-lint-dry-run.md](progress/reviewer/TASK-00013-04-review-config-lint-dry-run.md) が `done`、判定が合格、差し戻し事項なしであることを確認し、追加修正なしで Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)