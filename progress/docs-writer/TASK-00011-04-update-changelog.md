# TASK-00011-04 CHANGELOG へ v1.1.0 未リリース変更を追記

- Status: done
- Role: docs-writer
- Parent: TASK-00011
- Related IDs: REQ-00001
- 起票日: 2026-04-22

## 目的

TASK-00011 で追加した `.github/prompts/` の 2 prompt を、未リリースの v1.1.0 変更として `CHANGELOG.md` に反映する。

## 完了条件

- `CHANGELOG.md` に `Unreleased` セクションが追加されている、または既存 `Unreleased` セクションへ追記されている
- v1.1.0 相当の未リリース変更として以下 2 点が利用者向けに記載されている:
  - `.github/prompts/config-generator.prompt.md` の追加
  - `.github/prompts/model-recommender.prompt.md` の追加
- Keep a Changelog 形式を崩していない
- トレース ID を過剰に露出せず、利用者視点の簡潔な記述になっている

## スコープ外

- README や docs の更新
- prompt 本体の修正
- v1.1.0 のリリース日や版番号の確定

## 進捗ログ

- 2026-04-22 project-master: 子 task 起票。TASK-00011 の CHANGELOG 反映漏れ対応として docs-writer に委譲
- 2026-04-22 docs-writer: 着手。`CHANGELOG.md` に Unreleased セクションを追加し、prompt 2 件の未リリース変更を追記開始
- 2026-04-22 docs-writer: 完了。`CHANGELOG.md` の Unreleased / Added に prompt 2 件を反映し、Markdown エラーなしを確認
- 2026-04-22 docs-writer: reviewer 合格を確認し、本 task を `done` に更新。`verify.sh` は 10/10 OK

## レビュー記録 (reviewer 用)

- 未着手