# TASK-00014 v1.2.0 モデルプル / ウォームアップ / プロバイダ起動状態確認 CLI

- Status: done
- Role: project-master
- Related IDs: REQ-00001, FUN-00408, FUN-00409, FUN-00410, CLI-00112, CLI-00113, CLI-00114, CLI-00309, NFR-00001, NFR-00302, PROG-00103
- 起票日: 2026-04-22
- 完了日: 2026-04-24
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

## 委譲計画

- TASK-00014-01 solution-architect: `provider status` / `model pull` / `model warmup` の public surface、`system-probe` / `config dry-run` との責務境界、進捗表示 / 終了コード、既存 PVD-00402 / PVD-00406 の更新要否を確定する
- TASK-00014-05 reviewer: TASK-00014-01 の設計が実装着手条件を満たすか、docs/design に旧前提との矛盾や未確定情報が残っていないかを確認する
- TASK-00014-02 programmer: 設計確定後に `provider status` / `model pull` / `model warmup` を実装し、既存 CLI 非破壊と新規テストを確認する
- TASK-00014-03 docs-writer: README の v1.2.0 ロードマップ節とサブコマンド一覧を最終 public surface に合わせて更新する
- TASK-00014-04 reviewer: 設計・実装・README 更新を横断確認し、warmup 効果の実機確認を含めて最終判定する

## 子 task

- TASK-00014-01 solution-architect: provider status / model pull / model warmup 仕様と関連設計確定
- TASK-00014-05 reviewer: provider status / model pull / model warmup 設計確定レビュー
- TASK-00014-02 programmer: provider status / model pull / model warmup 実装とテスト
- TASK-00014-03 docs-writer: README の v1.2.0 / subcommand 記述更新
- TASK-00014-04 reviewer: provider status / model pull / model warmup 最終確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (Q1 採用 + プロバイダ起動状態確認追加) を踏まえ起票
- 2026-04-24 project-master: TASK-00014 を開始。現行 docs/design では [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) の PVD-00402 / PVD-00406 が model pull / warm-up を責務外としている一方、現行 trunk には `system-probe` / `config lint` / `config dry-run` が既に実装済みで、`provider status` / `model pull` / `model warmup` public surface は未実装であることを確認した。
- 2026-04-24 project-master: ユーザー再ヒアリングの結果、TASK-00014 は v1.2.0 に取り込み、公開面は `provider status` / `model pull` / `model warmup` を新設し、reviewer による warmup 効果の実機確認もスコープに含める方針を確定した。
- 2026-04-24 project-master: 設計差分の吸収を先行させるため TASK-00014-01 / 05 / 02 / 03 / 04 を起票した。solution-architect には `system-probe` / `config dry-run` との責務境界、PVD-00402 / PVD-00406 の扱い、進捗表示方針の確定を依頼する。
- 2026-04-24 solution-architect: TASK-00014-01 review-pending。FUN-00408 / FUN-00409 / FUN-00410、CLI-00112 / CLI-00113 / CLI-00114 / CLI-00309、FLW-00010 / 00011 / 00012、CFG-00608 / 00609 / 00610、PVD-00005 / PVD-00108〜00110 / PVD-00212〜00215 / PVD-00407 / PVD-00408、OOS-00012 を整理し、`provider status` / `model pull` / `model warmup` の public surface、暗黙 pull 禁止、`system-probe` / `config dry-run` との責務境界を設計へ反映した。
- 2026-04-24 reviewer: TASK-00014-05 done。設計レビューは合格、差し戻しは solution-architect task の Related IDs から OOS を除く progress 修正のみで解消し、programmer 着手可と判定した。
- 2026-04-24 programmer: TASK-00014-02 review-pending。`provider status` / `model pull` / `model warmup` を実装し、Ollama `/api/version` / `/api/tags` / `/api/pull` / minimal generate を標準ライブラリで扱う Provider preparation 基盤を追加した。`PYTHONPATH=src python -m unittest tests.test_providers tests.test_cli_phase3` は 46 tests、`PYTHONPATH=src python -m unittest tests.test_run_integration tests.test_compare_integration tests.test_smoke_checklist tests.test_cli_phase3 tests.test_providers` は 59 tests すべて成功、`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、`provider status --config-dir configs` は provider 未起動環境で想定どおり exit 9 を確認した。
- 2026-04-24 docs-writer: TASK-00014-03 review-pending。README に `provider status` / `model pull` / `model warmup` と既存 `system-probe` / `config lint` / `config dry-run` / `check` の使い分け、v1.2.0 の主導線を反映した。
- 2026-04-24 reviewer: TASK-00014-04 review-pending。初回レビューで README の旧「ollama pull / serve はユーザー側で実施」文言が新 public surface と矛盾すると指摘した一方、live Ollama smoke では `provider status` reachable、`model pull` already_present、`model warmup` ready (elapsed 12.06s)、warmup 後の `ollama ps` loaded を確認した。
- 2026-04-24 docs-writer: TASK-00014-03 review-pending。README の user-facing 文言を修正し、「provider 起動は前提」「model 取得は `model pull` または provider CLI の明示操作」「暗黙 pull はしない」に統一した。
- 2026-04-24 reviewer: TASK-00014-04 done。README blocker 解消後の focused recheck と `MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK を確認し、最終レビューを合格とした。
- 2026-04-24 solution-architect: TASK-00014-01 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 programmer: TASK-00014-02 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 docs-writer: TASK-00014-03 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 project-master: 子 task 完了を確認し、TASK-00014 を done に更新した。