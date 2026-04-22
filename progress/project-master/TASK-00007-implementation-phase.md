# TASK-00007 v1.0.0 実装フェーズ

- Status: done
- Role: project-master
- Related IDs: REQ-00001, ARCH-00001 (確定設計の代表 ID), COMP-00001/00004/00005/00006/00007/00008/00009/00010/00011/00012, NFR-00302

## 目的

v0.1.0 設計層が確定したため (TASK-00001..TASK-00006 done)、`docs/design/` および `docs/requirements/` を一次情報として v1.0.0 実装に着手する。中心目的 (REQ-00001) の最小実証として、1 モデルで `run` が完走し `compare` で 2 Run を束ねられる状態をゴールとする。

## スコープ方針

- 段階分割: Phase 1 (最小垂直スライス) → Phase 2 (Comparison/Report) → Phase 3 (scorer 全種・仕上げ)
- 実装言語: Python 3.13 + 標準ライブラリのみ (NFR-00302)
- Provider: v1 は Ollama のみ
- 設計と齟齬が生じた場合、まず設計側で更新可否を判断し、必要なら solution-architect に再委譲する

## Phase 1 完了条件 (最小垂直スライス)

- COMP-00007 Configuration Loader: 設定ファイル読込 + バリデーション
- COMP-00008 Task Catalog: TaskProfile 集合の読込
- COMP-00005 Provider Adapter (Ollama): 1 推論実行
- COMP-00006 Quality Scorer: 最低 1 種 (textual_match 系) 実装
- COMP-00004 Trial Aggregator: n=k Trial 集計
- COMP-00010 Run Coordinator: 1 Run = 1 Model のオーケストレーション
- COMP-00009 Result Store: Run 永続化 (JSON 等)
- COMP-00001 CLI Entry: `run` サブコマンド
- 1 モデル × 1 TaskProfile × n=3 Trial が完走し、Run 識別子と Run ファイルが出力される
- ユニットテスト + 設計依拠の最小受入テスト (FUN-00207 観点)

## Phase 2 完了条件

- COMP-00011 Run Comparator: 2+ Run を束ねた Comparison 生成 (DAT-00108 / DAT-00109)
- COMP-00012 Report Renderer: 品質軸/速度軸/統合軸ランキング出力
- CLI `compare` サブコマンド
- FUN-00308 観点の受入確認

## Phase 3 完了条件

- Quality Scorer 全種 (SCR- 系すべて)
- エラーハンドリング・終了コード・CLI ヘルプ整備
- v1.0.0 smoke (release-criteria.md チェックリスト) を通過

## 子 task

- TASK-00007-01 programmer: Phase 1 最小垂直スライス (done)
- TASK-00007-02 programmer: Phase 2 Comparison + Report + compare/report/comparisons CLI (done)
- TASK-00007-03 programmer: Phase 3 scorer 全種 + 仕上げ + smoke 通過 (done)
- TASK-00007-04 programmer: v1.0.0 manual smoke 実機実行 (done)

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票、Phase 1 を programmer に委譲
- 2026-04-19 programmer/reviewer: Phase 1 完了 (TASK-00007-01 done, 33 テスト OK)
- 2026-04-20 programmer/reviewer: Phase 2 完了 (TASK-00007-02 done, 49 テスト OK)
- 2026-04-20 project-master: Phase 3 を programmer に委譲 (TASK-00007-03)
- 2026-04-20 programmer/reviewer: Phase 3 完了 (TASK-00007-03 done, 119 テスト OK)
- 2026-04-20 programmer/reviewer: 実機 smoke 5 項目達成 (TASK-00007-04 done, qwen2.5:7b)
- 2026-04-20 project-master: 親 task クローズ。リリース準備は TASK-00008 へ移行
