# TASK-00010-01 README ロードマップ節を v1.1.0 / v1.2.0 / v2.0.0 構成に改訂

- Status: done
- Role: docs-writer
- Parent: TASK-00010
- Related IDs: REQ-00001
- 起票日: 2026-04-20

## 目的

v1.0.0 リリース後のヒアリング結果を [README.md](../../README.md) のロードマップ節に反映する。v1.1.0 区分を「コンフィグ生成プロンプト」に、新設 v1.2.0 を「環境確認とコンフィグ検証 CLI」に、v2.0.0 を「プロバイダ拡張と高次計測」に再編する。設計・実装は本 task では行わない (記述のみ)。

## 完了条件

- README の「## ロードマップ」節が v0.1.0 / v1.0.0 / v1.1.0 / v1.2.0 / v2.0.0 の 5 区分構成になっている。
- v0.1.0 / v1.0.0 区分は無改変。
- 既存の重複項目 (LM Studio / OpenAI 互換 provider 拡張、環境健全性確認コマンド) は新区分に統合され重複していない。
- 「過去 run 同士の比較・トレンド表示」「BYO-dataset を支援するテンプレートと検証コマンド」は削除されず温存されている。
- 末尾の「ロードマップは要求の変化に応じて見直します。…」の一文が維持されている。
- README 本文にトレース ID (REQ-/FUN-/A-F の符号) が含まれていない。
- `MMDC_REQUIRED=0 bash scripts/verify.sh` が成功する。

## スコープ外

- README 以外の文書 (CHANGELOG, release-criteria.md, out-of-scope.md 等) の更新。
- v1.1.0 / v1.2.0 / v2.0.0 機能の設計・実装。
- pyproject.toml の version 変更。

## 進捗ログ

- 2026-04-20 docs-writer: 起票。README 改訂に着手。
- 2026-04-20 docs-writer: README ロードマップ節を v0.1.0 / v1.0.0 / v1.1.0 / v1.2.0 / v2.0.0 の 5 区分に再編。重複していた provider 拡張・環境健全性確認は v2.0.0 / v1.2.0 に統合し、過去 run 比較・BYO-dataset テンプレートは v2.0.0 末尾の将来検討として温存。`MMDC_REQUIRED=0 bash scripts/verify.sh` の実行はユーザー側で確認 (本セッションは terminal 実行ツール不在のため未実行)。

## レビュー記録 (reviewer 用)

- (未実施)
