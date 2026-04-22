# Changelog

本ファイルの形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠する。
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [1.0.0] - 2026-04-20

v1.0.0 ミニマル実装リリース。「あなたの PC・あなたの用途で最適なローカル LLM を選ぶ」(REQ-00001) ための最小垂直スライスを提供する。受入基準の正本は [docs/development/release-criteria.md](docs/development/release-criteria.md)。

### Added

- 8 Component の最小実装 (COMP-00001..00012): CLI Entry, Configuration Loader, Task Profile / Model Candidate Registry, Provider Adapter (Ollama), Run Coordinator, Trial Executor, Scorer, Aggregator, Comparator, Result Store, Report Renderer
- CLI 全サブコマンド (CLI-00102..00108): `run` / `compare` / `report` / `runs` / `comparisons` / `list` / `check`
- 1 Run = 1 Model Candidate の Run 実行 (FUN-00207)、複数 Trial 実行と統計集計 (n / mean / p50 / p95、SCR-00401..00404)
- 複数 Run を束ねた Comparison とモデル横断ランキング (品質軸 / 速度軸 / 統合軸、SCR-00802..00804、FUN-00308)
- スコアラ SCR-00101..00107 (`exact_match` / `normalized_match` / `regex_match` / `contains` / `json_valid` / `length_within` / `numeric_close`)
- 機械可読 (JSON) と人間可読 (Markdown) の両出力 (FUN-00305、CLI-00201)
- Provider: Ollama 1 種 (PVD-00401)。既定接続先は `http://localhost:11434` (CFG-00204)
- 同梱サンプル `configs/` 一式 (TaskProfile / Model Candidate / Provider / Run × 2 / Comparison)
- Run / Comparison の進捗を標準エラーへ継続出力 (NFR-00501)
- 終了コード分類 (CLI-00301..00305): success / user-input / configuration / runtime / partial-failure
- LICENSE (BSD-3-Clause, Copyright (c) 2026 Taogya) を同梱

### Known Limitations

- Provider は Ollama のみ (REQ-00001 / OOS-00001)。LM Studio / OpenAI 互換 API は v1.1 以降
- 終了コード CLI-00306 (`EXIT_COMPARISON_INCOMPLETE` = 6) は v1.0.0 では予約のみ。`compare` 経路では未消費 (TaskProfile セット不一致は CLI-00302 で拒否)
- モデルの自動 download / 起動・停止は本ツールの責務外 (OOS-00005 / OOS-00006)。`ollama pull` / `ollama serve` はユーザー側で実施する
- LLM-as-a-Judge による自動採点なし (OOS-00004)。スコアラは決定的判定のみ
- streaming TTFT / decode TPS、RAM / GPU メモリ計測なし (OOS-00002 / OOS-00003)
- Run の途中再開・失敗 Case のみ再実行は未対応 (OOS-00009)
- CI 組み込み用の閾値 gate なし (OOS-00008)

[1.0.0]: https://semver.org/lang/ja/
