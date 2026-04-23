# TASK-00013 v1.2.0 config lint / dry-run サブコマンド

- Status: done
- Role: project-master
- Related IDs: REQ-00001, FUN-00406, FUN-00407, CLI-00110, CLI-00111, CLI-00308, NFR-00302, PROG-00103
- 起票日: 2026-04-22
- 完了日: 2026-04-23
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

## 委譲計画

- TASK-00013-01 solution-architect: `check` / `system-probe` / `config lint` / `config dry-run` の public surface、入力単位、終了コード、再利用境界を確定する
- TASK-00013-05 reviewer: TASK-00013-01 の設計が実装着手条件を満たすか、既存 docs/design と現行コードの責務境界に矛盾がないかを確認する
- TASK-00013-02 programmer: 設計確定後に `config lint` / `config dry-run` を実装し、既存 CLI 非破壊と新規テストを確認する
- TASK-00013-03 docs-writer: README の v1.2.0 ロードマップ節とサブコマンド一覧を最終 public surface に合わせて更新する
- TASK-00013-04 reviewer: 設計・実装・README 更新・sample config 検証結果を横断確認する

## 子 task

- TASK-00013-01 solution-architect: config lint / dry-run 仕様と関連設計確定
- TASK-00013-05 reviewer: config lint / dry-run 設計確定レビュー
- TASK-00013-02 programmer: config lint / dry-run 実装とテスト
- TASK-00013-03 docs-writer: README の v1.2.0 / subcommand 記述更新
- TASK-00013-04 reviewer: config lint / dry-run 最終確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (F 採用) を踏まえ起票
- 2026-04-23 project-master: TASK-00013 を開始。現行 trunk では `check` が静的整合性検証、`system-probe` が host/provider/model の動的観測として既に実装済みであり、README の `config lint / dry-run` 表現は public surface として未確定であることを確認した。
- 2026-04-23 project-master: 利用者視点では「生成済み TOML を静的に点検する面」と「run.toml 起点で実行せずに preflight する面」の 2 つが未実装だと整理した。責務境界の確定を先行させるため TASK-00013-01 / 05 / 02 / 03 / 04 を起票した。
- 2026-04-23 project-master: 未確定事項は public surface (`check` / `system-probe` 優先か、`config lint` / `config dry-run` 新設か)、`config lint` の入力単位、`config dry-run` の利用者向け位置づけ。ユーザー再ヒアリングを継続し、確定後に solution-architect 着手条件へ反映する。
- 2026-04-23 project-master: ユーザー再ヒアリングの結果、利用者向け主導線は `system-probe` → `config lint` → `config dry-run` → `run`、`config lint` は単一ファイルと設定ディレクトリの両対応で進める方針を確定した。
- 2026-04-23 solution-architect: TASK-00013-01 done。FUN-00406 / FUN-00407、FLW-00008 / FLW-00009、CLI-00110 / CLI-00111 / CLI-00308、CFG-00604〜00607 を採番し、`check` / `system-probe` / `config lint` / `config dry-run` の責務境界、単一ファイル lint の補助設定ソース境界、dry-run の 4 セクション出力と終了コードを設計へ反映した。
- 2026-04-23 reviewer: TASK-00013-05 done。設計レビューは合格、差し戻しなし。`config lint` の単一ファイル境界、`config dry-run` の CLI-00308、docs/design の確定情報粒度はいずれも妥当で、programmer 着手可と判定した。
- 2026-04-23 programmer: TASK-00013-02 review-pending。`config lint` / `config dry-run` を実装し、単一ファイル / config-dir lint、run 起点 preflight、provider probe 再利用、既存 CLI 非破壊テストを追加した。`PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_run_integration tests.test_providers` は 40 tests すべて成功、`config lint configs` と `config lint configs/run.toml --config-dir configs` は問題なし、`config dry-run configs/run.toml --config-dir configs` は想定どおり exit 8、`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK。
- 2026-04-23 docs-writer: TASK-00013-03 review-pending。README に `system-probe` → `config lint` → `config dry-run` → `run` の導線、`check` の既存互換位置づけ、`config lint` / `config dry-run` の利用者向け説明を反映した。
- 2026-04-23 reviewer: TASK-00013-04 done。public surface、責務境界、終了コード、異常系メッセージ、README 整合を確認し、`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、`PYTHONPATH=src python -m unittest tests.test_cli_phase3 tests.test_run_integration tests.test_providers` 40 tests OK、sample config の lint OK、dry-run negative の exit 8 を確認した。差し戻し事項なし。
- 2026-04-23 programmer: TASK-00013-02 done。reviewer 合格を受けて完了反映。
- 2026-04-23 docs-writer: TASK-00013-03 done。reviewer 合格を受けて完了反映。
- 2026-04-23 project-master: 子 task 完了を確認し、TASK-00013 を done に更新した。