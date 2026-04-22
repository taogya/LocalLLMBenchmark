# TASK-00014 v1.2.0 モデルプル / ウォームアップ / プロバイダ起動状態確認 CLI

- Status: open
- Role: project-master
- Related IDs: REQ-00001, NFR-00001, NFR-00302
- 起票日: 2026-04-22
- 対象バージョン: v1.2.0

## 目的

これまでユーザーが手作業で実施してきた「モデル pull」「初回ロード (ウォームアップ)」「プロバイダ
プロセスが起動しているかの確認」を CLI 化する。Run 実行前のコールドスタート分の計測ノイズを抑え、
NFR-00001 (個人開発者 5 分以内) 達成を支える。同時に v2.0.0 で計画する Web UI から呼び出す前提の
基盤コマンド群を v1.2.0 のうちに整備する位置付け。

## 完了条件

- 以下 3 系統のサブコマンド (または 1 サブコマンド + サブアクション) を提供:
  - `provider status`: 設定済み Provider のプロセス疎通 / バージョン / 利用可能モデル一覧を表示
  - `model pull`: 指定モデルを provider 経由で取得 (Ollama: `/api/pull` 等)
  - `model warmup`: 指定モデルへ最小プロンプトを 1 回投げてロード状態にする
- 進捗 (pull の MB 進捗 / warmup 完了) をユーザーに視認できる形で出力。
- 既存 system-probe (TASK-00012) / config lint (TASK-00013) と疎通確認基盤を共有する設計。
- 標準ライブラリのみで実装 (NFR-00302 維持)。
- README ロードマップ v1.2.0 区分・サブコマンド一覧に追記。

## スコープ外

- 自動アンロード / メモリ解放 (provider 側の責務)
- GUI / Web UI (v2.0.0)
- 非 Ollama provider 対応 (v2.0.0 の Provider Adapter 再設計後)

## 想定委譲計画 (着手時に確定)

- solution-architect: コマンド体系 (`provider status` 単独 vs `system-probe` 統合) と進捗表示方針を確定
- programmer: 実装 + テスト
- reviewer: コールドスタート抑止効果の確認 (manual smoke で warmup 有無を比較)

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (Q1 採用 + プロバイダ起動状態確認追加) を踏まえ起票