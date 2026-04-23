# TASK-00019-01 README / CHANGELOG v1.2.0 更新

- Status: done
- Role: docs-writer
- Parent: TASK-00019
- Related IDs: REQ-00001, NFR-00001
- 起票日: 2026-04-24

## 目的

README と CHANGELOG を v1.2.0 の公開面に合わせて更新し、利用者が provider preparation CLI を含む現行主導線を理解できる状態にする。README の `最短手順 (v1.0.0)` / `既知の制約 (v1.0.0)` 見出しも、現状に合う表現へ整理する。

## 完了条件

- README.md の `最短手順` / `既知の制約` の見出し version 表記が整理され、周辺見出しとの整合が取れている。
- README.md の最短手順と既知の制約が v1.2.0 の公開面 (`provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run`) と矛盾しない。
- CHANGELOG.md に 2026-04-24 付の [1.2.0] セクションが追加され、主要追加と既知の制約が利用者向けに要約されている。
- 利用者向け文書にトレース ID や内部実装詳細を露出していない。

## スコープ外

- release-criteria 更新 (TASK-00019-02)
- package version 更新 (TASK-00019-03)
- リリース前チェック最終判定 (TASK-00019-04)

## 進捗ログ

- 2026-04-24 project-master: 起票。README の section 見出し version 整理と CHANGELOG 1.2.0 追加を release docs 更新から分離した。
- 2026-04-24 docs-writer: [README.md](README.md) と [CHANGELOG.md](CHANGELOG.md) を確認し、README の `使い方の概観` / `最短手順` / `既知の制約` に残る旧 version 見出しと、CHANGELOG に v1.2.0 セクションが無いことを確認した。現行公開面は `provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run` / `run` で確定しているため、見出しは原則 version 無しに統一し、最短手順は v1.2.0 の主導線へ寄せる方針で着手した。
- 2026-04-24 docs-writer: [README.md](README.md) の `使い方の概観` / `最短手順` / `既知の制約` の見出しから version 表記を外し、最短手順を `provider status` -> `model pull` -> `model warmup` -> `system-probe` -> `config lint` -> `config dry-run` -> `run` の流れへ更新した。`check` は互換面として補足にとどめ、既知の制約の `EXIT_COMPARISON_INCOMPLETE` 注記も現行時点の表現へ整理した。
- 2026-04-24 docs-writer: [CHANGELOG.md](CHANGELOG.md) に 2026-04-24 付の [1.2.0] セクションを追加し、provider preparation CLI と preflight CLI を利用者向けに要約した。あわせて既存の v1.0.0 節から内部 ID 表記を外し、CHANGELOG 全体を user-facing な説明へ寄せた。
- 2026-04-24 docs-writer: [README.md](README.md), [CHANGELOG.md](CHANGELOG.md), [progress/docs-writer/TASK-00019-01-readme-changelog-v1-2-0.md](progress/docs-writer/TASK-00019-01-readme-changelog-v1-2-0.md) の診断を確認し、差し戻しに直結する問題が無いことを確認した。完了条件を満たしたため Status を `review-pending` に更新した。reviewer は README の最短手順が v1.2.0 公開面と矛盾しないこと、CHANGELOG 1.2.0 が user-facing で簡潔にまとまっていること、README / CHANGELOG に内部 ID が残っていないことを重点確認する。
- 2026-04-24 docs-writer: [progress/reviewer/TASK-00019-04-release-check-v1-2-0.md](../reviewer/TASK-00019-04-release-check-v1-2-0.md) で focused recheck を含む reviewer 判定が `done` になり、README / CHANGELOG に関する release blocker なしで合格したことを確認した。reviewer 合格を反映し、本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- 2026-04-24 reviewer: [progress/reviewer/TASK-00019-04-release-check-v1-2-0.md](../reviewer/TASK-00019-04-release-check-v1-2-0.md) にて合格。README の最短手順と CHANGELOG 1.2.0 節を含む v1.2.0 公開面の整合は維持され、docs-writer 観点の差し戻し事項はなし。