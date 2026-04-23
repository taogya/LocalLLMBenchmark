# Changelog

本ファイルの形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠する。
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠する。

## [1.2.0] - 2026-04-24

### Added

- `provider status` を追加し、provider の起動状態、版情報、利用可能 model 一覧を実行前に確認できるようにした
- `model pull` / `model warmup` を追加し、初回 Run 前の model 準備を CLI から明示実行できるようにした
- `system-probe` を追加し、host 情報、provider 疎通、登録済み model の可用性を 1 コマンドで確認できるようにした
- `config lint` / `config dry-run` を追加し、設定の静的確認と Run 前 preflight を本実行なしで行えるようにした

### Changed

- README の最短手順とサブコマンド導線を v1.2.0 の公開面に合わせて整理した
- `check` は既存ワークフロー向けの互換面として位置付けを明確化した

### Known Limitations

- Provider は引き続き Ollama のみ
- provider プロセスの起動・停止はユーザー側で行う。model 取得は `model pull` または provider CLI の明示操作のみで、暗黙 pull はしない
- `EXIT_COMPARISON_INCOMPLETE` (= 6) は引き続き予約のみで、`compare` 経路では未消費

## [1.1.0] - 2026-04-22

### Added

- askQuestions ベースで TaskProfile / Provider / Run / Comparison の TOML を個別生成できる config-generator prompt を追加
- provider / PC スペック / 用途を対話で聞き、候補モデルと選定理由を返す model-recommender prompt を追加

## [1.0.0] - 2026-04-20

v1.0.0 ミニマル実装リリース。「あなたの PC・あなたの用途で最適なローカル LLM を選ぶ」ための最小垂直スライスを提供する。受入基準の正本は [docs/development/release-criteria.md](docs/development/release-criteria.md)。

### Added

- CLI / configuration / scoring / run execution / comparison / reporting を含む最小実装一式を追加
- CLI サブコマンド `run` / `compare` / `report` / `runs` / `comparisons` / `list` / `check` を追加
- 1 Run = 1 Model Candidate の Run 実行、複数 Trial の統計集計 (n / mean / p50 / p95)、複数 Run の Comparison とランキングを追加
- 決定的 scorer (`exact_match` / `normalized_match` / `regex_match` / `contains` / `json_valid` / `length_within` / `numeric_close`) を追加
- 機械可読 (JSON) と人間可読 (Markdown) の両出力を追加
- Provider として Ollama を追加し、既定接続先を `http://localhost:11434` にした
- 同梱サンプル `configs/` 一式 (TaskProfile / Model Candidate / Provider / Run × 2 / Comparison)
- Run / Comparison の進捗を標準エラーへ継続出力するようにした
- success / user-input / configuration / runtime / partial-failure の終了コード分類を追加
- LICENSE (BSD-3-Clause, Copyright (c) 2026 Taogya) を同梱

### Known Limitations

- Provider は Ollama のみ。LM Studio / OpenAI 互換 API は v1.1 以降
- 終了コード `EXIT_COMPARISON_INCOMPLETE` (= 6) は v1.0.0 では予約のみ。`compare` 経路では未消費
- model の自動 download / pull と provider の起動・停止は v1.0.0 の責務外。`ollama pull` / `ollama serve` はユーザー側で実施する
- LLM-as-a-Judge による自動採点なし。scorer は決定的判定のみ
- streaming TTFT / decode TPS、RAM / GPU メモリ計測なし
- Run の途中再開・失敗 Case のみ再実行は未対応
- CI 組み込み用の閾値 gate なし

[1.0.0]: https://semver.org/lang/ja/
