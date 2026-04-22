# TASK-00004 1Run=1Model 改訂・OOS 追加・機械チェック整備

- Status: done
- Role: project-master
- Related IDs: REQ-00001..REQ-00009, FUN-001xx..004xx, NFR-00101, NFR-00303, ARCH-00102, ARCH-00203, COMP-00003, COMP-00004, DAT-00003, DAT-00004, FLW-00001, CLI-, CFG-, PVD-, SCR-, TRC-

## 目的

ユーザー報告 (2026-04-19) に基づく以下を一括対応する。

1. tmp/v0.1.0 参照の除去 (本プロジェクトを初版とする立場で書き直し)
2. Copilot CLI (raptor mini) 活用検討を `OOS-00011` として独立追加
3. 1 Run = 1 Model への設計改訂 (provider 制御をユーザー責務とする立場と整合)
4. Mermaid 図中の `<br/>` を `<br>` に修正、その他構文不正を点検
5. `scripts/traceability/` 配下に機械チェックスクリプト群を整備
6. その他機械チェックスクリプト追加 (実装漏れ・ロール境界・OOS 静的検査・Markdown/Mermaid 構文)

## 完了条件

- 全子 task が `done` または `review-pending` (reviewer 確認後 `done`)
- 設計層・要件層・表面層・README が新方針 (1 Run = 1 Model + Comparison) で整合
- 既存 ID は意味を変えず、変更分は新 ID + `superseded by` 併記方式
- `scripts/traceability/` 配下のスクリプト群が動作し、現リポジトリで違反 0 件 (または既知許容項目のみ)

## 子 task

- TASK-00004-01 solution-architect: 設計大改訂 (要件 → アーキ → 表面層、tmp 参照除去、OOS-00011、Mermaid 構文修正)
- TASK-00004-02 docs-writer: README 更新 (1 Run = 1 Model 反映、ロードマップ整合)
- TASK-00004-03 programmer: scripts/traceability/ + verify.sh 実装と現状違反の修正提案
- TASK-00004-04 reviewer: 全体最終確認 + スクリプト実行確認

## 進め方

1. TASK-00004-01 を先行 (設計層が後段の入力)
2. TASK-00004-02 と TASK-00004-03 を並行
3. TASK-00004-04 で総点検

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票。ユーザーヒアリング完了 (1Run=1Model 採用、OOS-00011 独立、scripts/traceability 整備、Mermaid 修正)
- 2026-04-19 solution-architect: TASK-00004-01 完了 (review-pending)。設計大改訂 13 ファイル、supersede 22 件、OOS-00011 追加、Mermaid 10 件修正、tmp/v0.1.0 参照除去
- 2026-04-19 docs-writer: TASK-00004-02 完了 (review-pending)。README に 1Run=1Model + Comparison 反映
- 2026-04-19 programmer: TASK-00004-03 完了 (review-pending)。scripts/traceability/ に 10 スクリプト + verify.sh 実装。active task の Related IDs OOS- 含有 3 件を検出
- 2026-04-19 project-master: 検出された 3 件 (TASK-00001 / TASK-00004 / TASK-00004-01) の Related IDs から OOS- を除去 (本文記述は維持)
- 2026-04-19 reviewer: TASK-00004-04 完了 (done)。verify.sh 全 10/10 OK。ユーザー報告可
- 2026-04-19 project-master: 親 task クローズ
