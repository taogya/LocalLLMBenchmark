# TASK-00012 v1.2.0 system-probe サブコマンド

- Status: done
- Role: project-master
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-22
- 完了日: 2026-04-23
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

## 委譲計画

- TASK-00012-01 solution-architect: `system-probe` の出力スキーマ、Provider Adapter / `model_candidates.toml` との結合点、既存 `check` と将来 `config lint` の責務境界を設計する
- TASK-00012-05 reviewer: TASK-00012-01 の設計が実装着手条件を満たすか、docs/design に未確定情報を混入させていないかを確認する
- TASK-00012-02 programmer: 設計確定後に `system-probe` を実装し、既存 7 サブコマンド非破壊をテストで確認する
- TASK-00012-03 docs-writer: README の v1.2.0 ロードマップ節とサブコマンド一覧へ `system-probe` を反映する
- TASK-00012-04 reviewer: 設計・実装・README 更新の整合、model-recommender prompt との接続性、NFR-00302 遵守を最終確認する

## 子 task

- TASK-00012-01 solution-architect: system-probe 仕様と関連設計確定
- TASK-00012-05 reviewer: system-probe 設計確定レビュー
- TASK-00012-02 programmer: system-probe 実装とテスト
- TASK-00012-03 docs-writer: README の v1.2.0 / subcommand 記述更新
- TASK-00012-04 reviewer: system-probe 最終確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (C 採用) を踏まえ起票
- 2026-04-22 project-master: TASK-00012 を開始。現行 trunk に `check` サブコマンドが既に存在し、README 上の「config lint / dry-run」表現と責務境界の整理が必要であることを確認
- 2026-04-22 project-master: ユーザー確認の結果、`check` 拡張で足りるなら既存活用、新責務があるなら別 CLI も許容と整理。TASK-00012-01 で境界判断を行う方針とした
- 2026-04-22 project-master: README 更新要件に合わせ docs-writer を委譲計画へ追加し、TASK-00012-01..04 を起票
- 2026-04-22 solution-architect: TASK-00012-01 が review-pending。FUN-00404 / FUN-00405、CLI-00109 / CLI-00307、CFG-00601〜00603、PVD-00004 / PVD-00106〜00107 / PVD-00209〜00211 / PVD-00406、FLW-00007 を採番し、`check` は静的検証、`system-probe` は動的観測、将来の `config lint` / `dry-run` はその周辺責務として整理
- 2026-04-22 project-master: 実装着手前提の設計確定は reviewer 確認待ち。未解決事項は TASK-00013 での名称整理 (`config lint` を新 public surface にするか、`check` を互換 alias として残すか) と、GPU 取得コマンド優先順位の実装確定
- 2026-04-23 project-master: docs/design に「実装で確定する」「将来の config lint / dry-run」といった未確定候補が混在していないかを別 task で監査することにし、TASK-00012 の実装ブロッカー解消用に TASK-00012-05 を追加
- 2026-04-23 reviewer: TASK-00012-05 done。TASK-00012-01 の設計は programmer 着手可能な粒度で確定しており、TASK-00018 に切り出した docs/design 運用論点は TASK-00012 の blocker ではないと確認
- 2026-04-23 solution-architect: TASK-00012-01 done。reviewer 合格を受けて system-probe 設計を確定
- 2026-04-23 programmer: TASK-00012-02 review-pending。`system-probe` 実装、Ollama probe 契約、CLI / provider / integration テスト追加、`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK を報告
- 2026-04-23 docs-writer: TASK-00012-03 review-pending。README の v1.2.0 節とサブコマンド一覧へ `system-probe` を反映
- 2026-04-23 reviewer: TASK-00012-04 done。4 セクション出力、標準ライブラリ制約、既存 7 サブコマンド非破壊、README 整合を確認。`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、42 tests OK
- 2026-04-23 programmer: TASK-00012-02 done。reviewer 合格を受けて完了反映
- 2026-04-23 docs-writer: TASK-00012-03 done。reviewer 合格を受けて完了反映
- 2026-04-23 project-master: 子 task 完了を確認し、TASK-00012 を done に更新