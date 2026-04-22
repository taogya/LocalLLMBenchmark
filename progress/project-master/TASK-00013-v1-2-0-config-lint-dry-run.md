# TASK-00013 v1.2.0 config lint / dry-run サブコマンド

- Status: open
- Role: project-master
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-22
- 対象バージョン: v1.2.0

## 目的

TaskProfile / Provider / Run / Comparison 設定の整合性を Run 実行前に検証する `config lint` (静的検証) と
`config dry-run` (Provider 疎通とモデル解決まで実施し実コールはしない) サブコマンドを追加する。
v1.1.0 のコンフィグ生成プロンプトが出力した TOML を即検証できる受け皿として機能させる。

## 完了条件

- `local-llm-benchmark config lint <path>` が以下を検出:
  - 必須キー欠落 / 型不一致 / 既知列挙値外 / 相互参照切れ (TaskProfile ↔ prompt set, Run ↔ Provider/TaskProfile/Comparison など)
  - 出力は人間可読サマリ + 終了コード (0=OK, 非0=NG)
- `local-llm-benchmark config dry-run <run.toml>` が以下まで実施:
  - Provider 疎通 (system-probe と共通基盤を再利用)
  - 指定モデルの解決可否
  - 1 case の prompt 組立まで (実 inference は実行しない)
- 既存 sample (`configs/run.toml` 等) で OK 判定が出る。
- README ロードマップ v1.2.0 区分・サブコマンド一覧に追記。
- 標準ライブラリのみで実装 (NFR-00302 維持)。

## スコープ外

- 設定自動修復 / 推奨値提示 (将来検討)
- ベンチ本実行への組込み (lint は明示コマンドのみ。Run 開始時の自動実行は別 task で要否判断)

## 想定委譲計画 (着手時に確定)

- solution-architect: lint ルール一覧 / dry-run 範囲 / 終了コード規約を確定
- programmer: 実装 + テスト (既存 Configuration Loader / Provider Adapter を再利用)
- reviewer: 既存 sample での OK 判定 / 異常系の具体エラーメッセージ確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (F 採用) を踏まえ起票