# TASK-00005 Mermaid 描画エラー修正

- Status: done
- Role: project-master
- Related IDs: PROG-00103

## 目的

ユーザー報告 (2026-04-19): VS Code プレビューで mermaid 図が "No diagram type detected" として描画されない。設計判断ができない状況のため緊急対応する。

## 完了条件

- `docs/` 配下の全 mermaid 図が描画可能になる
- `mmdc` ベースの厳格チェックが導入される

## 子 task

- TASK-00005-01 programmer: Mermaid 図の実描画エラー修正と検証強化

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票。programmer に委譲
- 2026-04-19 programmer: TASK-00005-01 完了。mmdc 11.12.0 + Chrome 131 で全 9 ブロックパス、構文起因の修正不要。check_mermaid_syntax.py に MMDC_REQUIRED=1 モード追加
- 2026-04-19 project-master: VS Code プレビュー拡張起因の可能性をユーザーに報告して親 task クローズ
