# TASK-00016 v2.0.0 LM Studio / llama.cpp server プロバイダ実装

- Status: open
- Role: project-master
- Related IDs: REQ-00001, COMP-00005
- 起票日: 2026-04-22
- 対象バージョン: v2.0.0
- 前提: TASK-00015 (Provider Adapter 抽象再設計) done

## 目的

TASK-00015 で確定した新 Provider Adapter 抽象に基づき、LM Studio / llama.cpp server (および可能な範囲で
OpenAI 互換エンドポイント) を v1 の Ollama Provider と同等に扱えるよう実装する。同一 prompt set で
複数バックエンドを横断比較できる状態を v2.0.0 のリリース要件にする。

## 完了条件

- 各 provider 実装が `local-llm-benchmark run` から呼び出し可能。
- v1 で動いていた Ollama Provider が新抽象でも回帰なく動作する。
- `configs/` に各 provider の sample TOML を同梱。
- 実機 smoke で「同一 prompt を 2 種以上の provider で実行 → Comparison でランキング表示」まで成功。
- 既存テスト全件 OK + 各 provider のユニットテスト追加。
- README ロードマップ v2.0.0 区分・サブコマンド一覧 (provider 一覧) に追記。

## スコープ外

- streaming TTFT / decode TPS の本実装 (別 task で要否判断)
- RAM / GPU メモリ計測 (別 task)
- Web UI からの provider 操作 (TASK-00017 設計範囲)

## 想定委譲計画 (着手時に確定)

- solution-architect: 各 provider の認証 / endpoint / モデル指定方式の差分整理
- programmer: 実装 + テスト + sample provider config
- reviewer: 横断比較 smoke / v1 互換確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (D 採用) を踏まえ起票