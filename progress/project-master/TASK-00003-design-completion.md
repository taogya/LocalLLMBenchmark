# TASK-00003 実装着手前の上位設計補完

- Status: done
- Role: project-master
- Related IDs: REQ-00001, FUN-001xx〜004xx, NFR-00001〜00602, ARCH-00001〜00302, COMP-00001〜00009, DAT-00001〜00202, FLW-00001〜00103, PROG-00103

## 目的

v1.0.0 実装着手の前提として、上位工程ドキュメントの不足を補い、設計を確定させる。

## 完了条件

- 以下が `docs/` に追加され、既存設計と整合している
  - CLI コマンド面 (`docs/design/05-cli-surface.md`)
  - 設定ファイル構成 (`docs/design/06-configuration-sources.md`)
  - Provider Adapter 契約 (`docs/design/07-provider-contract.md`)
  - Scoring + Ranking 規則 (`docs/design/08-scoring-and-ranking.md`)
  - 環境前提と依存方針 (`docs/development/environment.md`)
  - v1.0.0 受入基準 (`docs/development/release-criteria.md`)
- README が新規ドキュメントを参照し、ロードマップと整合
- reviewer が設計セット全体を確認し、ユーザー報告可と判定

## スコープ外

- 実装コード、テストコード
- v1.1 以降のドキュメント

## 子 task

- TASK-00003-01 solution-architect: 設計ドキュメント 6 件追加
- TASK-00003-02 docs-writer: README 更新 (新規ドキュメント参照・ロードマップ整合)
- TASK-00003-03 reviewer: 設計セット最終確認

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票。不足ドキュメントを 6 件特定
- 2026-04-19 solution-architect: TASK-00003-01 完了。docs/design/05-08, docs/development/{environment,release-criteria}.md を新規作成、traceability に CLI-/CFG-/PVD-/SCR- を追記
- 2026-04-19 docs-writer: TASK-00003-02 完了。README に新規 6 件のリンクと参照を反映
- 2026-04-19 reviewer: TASK-00003-03 完了 (done)。所見は report 可。軽微修正 1 件のみ実施 (README L56 表記)
- 2026-04-19 project-master: 親 task クローズ。残課題は別 task で扱う
