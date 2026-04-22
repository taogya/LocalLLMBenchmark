# TASK-00012 v1.2.0 system-probe サブコマンド

- Status: open
- Role: project-master
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-22
- 対象バージョン: v1.2.0

## 目的

実行環境の CPU / メモリ / GPU / OS を自動取得し、モデル選定 (v1.1.0 の model-recommender prompt) や
コンフィグ検証 (v1.2.0 の config lint) の入力として再利用できる `system-probe` サブコマンドを追加する。
provider 疎通とモデル可用性確認も同コマンドに含め、初回ベンチ前のチェックを 1 コマンドに集約する。

## 完了条件

- `local-llm-benchmark system-probe` が以下を出力 (Markdown / JSON 切替):
  - CPU 種別 / 物理コア / 論理コア / メモリ容量 / OS / GPU 検知結果
  - 設定済み Provider への疎通結果 (Ollama: `/api/tags` 等)
  - 設定済み `model_candidates.toml` に列挙されたモデルの可用性 (provider 側に存在するか)
- 出力は v1.1.0 model-recommender prompt が参照可能な JSON 形式を含む。
- 標準ライブラリ + 既存 Provider Adapter のみで実装 (NFR-00302 維持)。
- README ロードマップ v1.2.0 区分・サブコマンド一覧に追記。
- 既存 7 サブコマンドの動作・I/O に影響しない (非破壊)。

## スコープ外

- モデルの自動 pull / ウォームアップ (TASK-00014 で対応)
- 設定整合性検証 (TASK-00013 で対応)
- GPU の詳細ベンチ計測 (v2.0.0 streaming/RAM 計測スコープ)

## 想定委譲計画 (着手時に確定)

- solution-architect: system-probe の出力スキーマ / Provider Adapter との結合点設計
- programmer: 実装 + テスト
- reviewer: 出力スキーマと model-recommender prompt の整合 / NFR-00302 遵守確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (C 採用) を踏まえ起票