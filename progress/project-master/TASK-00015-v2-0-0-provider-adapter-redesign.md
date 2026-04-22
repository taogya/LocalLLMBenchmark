# TASK-00015 v2.0.0 Provider Adapter 抽象再設計

- Status: open
- Role: project-master
- Related IDs: REQ-00001, COMP-00005
- 起票日: 2026-04-22
- 対象バージョン: v2.0.0
- 区分: 設計のみ

## 目的

v1 系で意図的に「Ollama only」に閉じていた Provider Adapter (COMP-00005) を、複数バックエンド
(LM Studio / llama.cpp server / OpenAI 互換エンドポイント等) を同じ抽象で扱えるよう再設計する。
TASK-00016 (LM Studio / llama.cpp server 実装) の前提となる設計タスク。provider 設定スキーマの
後方互換は破壊する可能性が高いため major 昇格 (v2.0.0) とする。

## 完了条件

- 以下が `docs/design/` 配下にまとまっている:
  - 抽象 I/F (request / response / error / streaming 余地) の確定
  - provider 種別ごとの差分表 (Ollama / LM Studio / llama.cpp server / OpenAI 互換)
  - provider 設定スキーマ案と v1 からの移行ガイドライン
  - streaming TTFT / decode TPS 計測拡張余地の検討メモ (実装は別 task)
- 受入基準として `release-criteria.md` の v2.0.0 区分に ID 単位で展開される。
- 実装は **本 task では行わない** (TASK-00016 で着手)。

## スコープ外

- 各 provider の実装 (TASK-00016)
- streaming / RAM・GPU 計測の実装 (将来 task)
- Web UI 設計 (TASK-00017)

## 想定委譲計画 (着手時に確定)

- solution-architect: 抽象 I/F と移行ガイドの設計
- reviewer: 後方互換影響と移行コスト評価

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (R1 採用) を踏まえ起票