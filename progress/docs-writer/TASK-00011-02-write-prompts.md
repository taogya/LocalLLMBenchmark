# TASK-00011-02 `.github/prompts/` 本体執筆

- Status: done
- Role: docs-writer
- Parent: TASK-00011
- Related IDs: REQ-00001
- 起票日: 2026-04-22

## 目的

TASK-00011-01 で確定した prompt 仕様に基づき、`.github/prompts/` 配下へ利用者向け prompt 本体を追加する。

## 完了条件

- TASK-00011-01 で確定した prompt 群が `.github/prompts/` 配下に実装されている
- 各 prompt の冒頭に目的・前提・出力先が明記されている
- 利用者視点で短く読め、トレース ID を含まない
- コンフィグ生成 prompt は出力先フォルダ確認を含み、sample config 上書き回避が明示されている
- model-recommender prompt は provider 先行ヒアリングと Web 情報参照方針を反映している

## スコープ外

- prompt 仕様の変更 (TASK-00011-01 で確定)
- 最終レビュー (TASK-00011-03)

## 進捗ログ

- 2026-04-22 project-master: 子 task 起票。TASK-00011-01 の完了待ち
- 2026-04-22 docs-writer: Status を `in-progress` に更新。TASK-00011-01 を正本として `.github/prompts/` 配下の 2 prompt 執筆に着手
- 2026-04-22 docs-writer: `.github/prompts/config-generator.prompt.md` と `.github/prompts/model-recommender.prompt.md` を追加。config-generator には 4 種別ごとの askQuestions、最小 TOML 項目、sample 上書き禁止、Run 時の model_candidate 制約を反映した
- 2026-04-22 docs-writer: model-recommender には provider 先行ヒアリング、公式情報優先、Web 不可時フォールバック、Ollama の benchmark 実行整合注記を反映し、関連 3 ファイルのエラー確認後に Status を `done` へ更新

## レビュー記録 (reviewer 用)

- 未着手