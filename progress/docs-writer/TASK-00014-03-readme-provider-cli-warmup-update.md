# TASK-00014-03 README の v1.2.0 / subcommand 記述更新

- Status: done
- Role: docs-writer
- Parent: TASK-00014
- Related IDs: REQ-00001
- 起票日: 2026-04-24

## 目的

`provider status` / `model pull` / `model warmup` の名称と利用者向け説明が確定したら、README の v1.2.0 ロードマップ節とサブコマンド一覧へ反映する。利用者が `system-probe` / `config lint` / `config dry-run` と今回の 3 コマンドの役割分担を理解できる状態にする。

## 完了条件

- 着手時点で TASK-00014-01 が `done`、TASK-00014-02 が少なくとも `review-pending` になっている。
- README の v1.2.0 ロードマップ節に最終 public surface と役割が反映されている。
- README のサブコマンド一覧に最終 public surface が追加または整理され、既存説明と矛盾しない。
- 利用者向け記述にトレース ID や内部実装詳細を露出していない。

## スコープ外

- 設計文書更新 (TASK-00014-01)
- `provider status` / `model pull` / `model warmup` 実装 (TASK-00014-02)
- 最終レビュー (TASK-00014-04)

## 進捗ログ

- 2026-04-24 project-master: 起票。README 更新要件を親 task の完了条件から分離するため作成。
- 2026-04-24 project-master: 利用者向けには、既存 `system-probe` / `config lint` / `config dry-run` との使い分けが読めることを重視し、内部実装や provider 固有 endpoint の説明は持ち込まない方針を共有。
- 2026-04-24 docs-writer: ユーザー前提と関連 task を確認し、TASK-00014-01 は設計レビュー合格済みの `review-pending`、TASK-00014-02 は `review-pending` であることから着手条件を満たすと判断した。[README.md](README.md), [progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md](progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md), [progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md](progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md), [progress/programmer/TASK-00014-02-implement-provider-cli-warmup.md](progress/programmer/TASK-00014-02-implement-provider-cli-warmup.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md) を確認し、README の更新対象を v1.2.0 ロードマップ節とサブコマンド一覧に限定して着手した。
- 2026-04-24 docs-writer: [README.md](README.md) の v1.2.0 ロードマップ節とサブコマンド一覧を更新し、`provider status` / `model pull` / `model warmup` を追加した。`provider status` / `model pull` / `model warmup` は provider / model 準備、`system-probe` / `config lint` / `config dry-run` は実行前確認として短く整理し、内部実装詳細や provider 固有 endpoint は記載していない。
- 2026-04-24 docs-writer: [README.md](README.md) と [progress/docs-writer/TASK-00014-03-readme-provider-cli-warmup-update.md](progress/docs-writer/TASK-00014-03-readme-provider-cli-warmup-update.md) の診断を確認し、問題がないことを確認した。完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-24 docs-writer: reviewer 差し戻し対応として [README.md](README.md) の旧運用文言を最小修正した。前提環境・最短手順・既知の制約で、provider 起動はユーザー側、model 取得は `model pull` または provider CLI の明示操作、暗黙 pull は行わないという利用者向け説明に統一し、Status は `review-pending` のまま reviewer 再確認待ちとした。
- 2026-04-24 docs-writer: [progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md](progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md) が `done` / 合格になったことを確認した。README の user-facing 文言整合性に関する blocker 解消が reviewer で確認済みのため、本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- 2026-04-24 reviewer: [progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md](progress/reviewer/TASK-00014-04-review-provider-cli-warmup.md) で `done` / 合格。README の user-facing 文言は `provider status` / `model pull` / `model warmup` の主導線と整合し、前回 blocker は解消済み。