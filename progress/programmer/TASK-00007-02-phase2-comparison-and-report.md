# TASK-00007-02 Phase 2 Comparison + Report Renderer + compare CLI

- Status: done
- Role: programmer
- Parent: TASK-00007
- Related IDs: COMP-00011, COMP-00012, COMP-00001, DAT-00009, DAT-00010, DAT-00011, DAT-00108, DAT-00109, FUN-00301, FUN-00308, CLI-00102, CLI-00107, CLI-00108, SCR-00601, SCR-00602, SCR-00701, SCR-00801..00807, NFR-00302

## 目的

Phase 1 で完成した 1 Run = 1 Model 実行系の上に、複数 Run を束ねて比較する Comparison 系を実装する。`compare` サブコマンドで 2 件以上の Run を入力すると Comparison が生成され、品質軸 / 速度軸 / 統合軸でランキング付き Markdown レポートが出力される状態をゴールとする。

## 一次情報 (必読)

- [docs/design/02-components.md](../../docs/design/02-components.md) (COMP-00011 Run Comparator, COMP-00012 Report Renderer)
- [docs/design/03-data-model.md](../../docs/design/03-data-model.md) (DAT-00009 Comparison, DAT-00010 RankedItem, DAT-00011 ComparisonReport, DAT-00108/00109 不変条件)
- [docs/design/04-workflows.md](../../docs/design/04-workflows.md) (FLW-00006 Comparison シーケンス)
- [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) (CLI-00102 report, CLI-00107 compare, CLI-00108 comparisons)
- [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md) (CFG-00207, CFG-00506)
- [docs/design/08-scoring-and-ranking.md](../../docs/design/08-scoring-and-ranking.md) (SCR-00601..00807 集約・ランキング・統合スコア)
- [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md) (FUN-00301, FUN-00308)
- [docs/development/release-criteria.md](../../docs/development/release-criteria.md) (smoke 観点チェックリスト)

## スコープ (実装対象)

| 区分 | 内容 |
| --- | --- |
| COMP-00011 Run Comparator | 2 件以上の Run から Comparison を生成 (DAT-00108/00109 不変条件遵守、違反時はエラー) |
| COMP-00012 Report Renderer | Comparison から Markdown 形式の ComparisonReport を生成 (品質軸/速度軸/統合軸ランキング) |
| 設定 (CFG-00207) | Comparison 入力 (2 件以上の Run 識別子集合 + 重み等) を受ける物理スキーマ確定と Loader 拡張 |
| Result Store 拡張 | Comparison / ComparisonReport の永続化 (既存 Run と同等の構造) |
| CLI `compare` (CLI-00107) | 複数 Run を束ねて Comparison を生成、Comparison 識別子を返す |
| CLI `report` (CLI-00102) | 既存 Run または Comparison を入力に Markdown レポート出力 |
| CLI `comparisons` (CLI-00108) | 保存済み Comparison の一覧表示 |
| ユニット/結合テスト | 各 Component と CLI 経路 |

## 完了条件

- 上記 Component が設計仕様に沿って実装されている
- `compare` サブコマンドで 2 件以上の Run から Comparison が生成され、識別子が返る
- DAT-00108 / DAT-00109 違反 (Run 1 件以下、TaskProfile セット不一致) は明示的にエラー終了する
- `report` サブコマンドで Comparison の Markdown ランキングが出力される (品質軸/速度軸/統合軸の 3 区分)
- `comparisons` サブコマンドで保存済み Comparison が一覧できる
- 統合スコア重み (SCR-00806 `w_quality=0.7` / SCR-00807 `w_speed=0.3`) が適用されている (再評価注記は実装側 docstring にも反映)
- ユニットテスト + 結合テスト追加 (FUN-00308 観点)
- Python 3.13 + 標準ライブラリのみ (NFR-00302)
- `pytest` または `python -m unittest` パス
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK

## 制約

- 過剰実装禁止 (Phase 3 の scorer 全種拡充・追加サブコマンドは対象外)
- 外部ライブラリ追加禁止 (NFR-00302)
- Phase 1 で実装済みの Configuration Loader / Task Catalog / Run Coordinator / Result Store / Provider Adapter / Quality Scorer の **意味を変えない**。拡張のみ。
- 設計と齟齬が出た場合は実装を中断して project-master に報告 (設計を先に直す方針)
- コメント・docstring・CLI メッセージは日本語

## 検証

- ユニット/結合テスト
  - 結合テストでは Phase 1 の Provider モックを再利用し、`run` を 2 回 → `compare` → `report` の流れを 1 ケース通すこと
- `MMDC_REQUIRED=1 bash scripts/verify.sh` (mmdc 未導入なら `bash scripts/verify.sh` で代替し進捗ログに明記)

## 報告

- 追加・変更したファイルの絶対パス一覧
- 実装した Component と参照した設計 ID の対応
- テスト実行結果 (件数・成否)
- verify.sh 実行結果
- 設計と齟齬があった場合の内容と対応
- 残課題 / Phase 3 への申し送り

## 進捗ログ

- 2026-04-20 project-master: 起票
- 2026-04-20 programmer: Phase 2 実装と検証を完了。追加・変更ファイル:
  - src/local_llm_benchmark/models.py (Comparison/ComparisonReport/RankedItem/ComparisonWeights/ModelComparisonSummary/RANKING_AXIS_* を追加)
  - src/local_llm_benchmark/storage/__init__.py (write_comparison/list_comparisons/load_comparison/load_aggregation/generate_comparison_id 追加、list_runs から comparisons/ 除外)
  - src/local_llm_benchmark/orchestration/comparator.py (新規 COMP-00011, ComparisonError と DAT-00108/00109 違反検出)
  - src/local_llm_benchmark/orchestration/__init__.py (RunComparator/ComparisonError の export)
  - src/local_llm_benchmark/config/loader.py (CFG-00207 ComparisonConfig + load_comparison_config)
  - src/local_llm_benchmark/config/__init__.py (export 追加)
  - src/local_llm_benchmark/reporting/__init__.py (新規 COMP-00012 export)
  - src/local_llm_benchmark/reporting/renderer.py (新規 render_run_markdown / render_comparison_markdown)
  - src/local_llm_benchmark/cli/main.py (run/compare/report/comparisons の 4 サブコマンドへ再構成)
  - tests/test_comparator.py / tests/test_reporting.py / tests/test_comparison_config.py / tests/test_compare_integration.py (新規)
- 2026-04-20 programmer: 検証結果。`python -m unittest discover -s tests` 49 件すべて成功。`MMDC_REQUIRED=1 bash scripts/verify.sh` 10 チェック全 OK (初回 check_id_references で未定義 ID 参照 1 件が発生したため Related IDs から削除して再実行し全 OK を確認)。設計との齟齬は無し。Phase 3 への申し送り: (1) scorer 種拡充 (jaccard / json schema 等)、(2) `comparisons --as report` などの利便コマンド、(3) report の HTML/CSV 出力、(4) Comparison メタにスキーマバージョン追加の要否検討。
- 2026-04-20 reviewer: 最終レビュー完了。観点 10 項目すべて OK。`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、`python -m unittest discover -s tests` 49/49 成功を再現確認。COMP-00011/00012・DAT-00108/00109・SCR-00805..00809・CFG-00207・CLI-00102/00107/00108 が設計通り実装されている。Phase 1 既存モジュールは追加のみ (list_runs から `comparisons/` を除外する変更は安全な拡張)。NFR-00302 違反なし (tomllib/dataclasses/json のみ)。Phase 3 範囲混入なし (EXIT_COMPARISON_INCOMPLETE は予約として明記)。`done` に更新。
