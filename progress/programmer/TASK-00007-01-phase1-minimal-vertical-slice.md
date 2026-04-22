# TASK-00007-01 Phase 1 最小垂直スライス実装

- Status: done
- Role: programmer
- Parent: TASK-00007
- Related IDs: COMP-00001, COMP-00004, COMP-00005, COMP-00006, COMP-00007, COMP-00008, COMP-00009, COMP-00010, FUN-00207, NFR-00302, NFR-00001

## 目的

v1.0.0 の最小垂直スライスを実装する。1 モデル × 1 TaskProfile × n=3 Trial が `run` サブコマンドで完走し、Run 識別子と Run ファイルが返る状態をゴールとする。

## 一次情報 (必読)

- [docs/requirements/01-overview.md](../../docs/requirements/01-overview.md) (REQ- 系)
- [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md) (FUN-00207 ほか)
- [docs/requirements/03-non-functional.md](../../docs/requirements/03-non-functional.md) (NFR-00001, NFR-00302 ほか)
- [docs/design/01-architecture.md](../../docs/design/01-architecture.md)
- [docs/design/02-components.md](../../docs/design/02-components.md) (COMP- 系)
- [docs/design/03-data-model.md](../../docs/design/03-data-model.md) (DAT- 系)
- [docs/design/04-workflows.md](../../docs/design/04-workflows.md) (FLW- 系)
- [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) (CLI-)
- [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md) (CFG-)
- [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) (PVD-)
- [docs/design/08-scoring-and-ranking.md](../../docs/design/08-scoring-and-ranking.md) (SCR-)
- [docs/development/environment.md](../../docs/development/environment.md)
- [docs/development/release-criteria.md](../../docs/development/release-criteria.md)

## スコープ (実装対象)

| Component | 役割 (要約) |
| --- | --- |
| COMP-00007 Configuration Loader | TOML 設定読込・バリデーション |
| COMP-00008 Task Catalog | TaskProfile 集合の読込 |
| COMP-00005 Provider Adapter (Ollama) | 推論実行 (Ollama 1 種) |
| COMP-00006 Quality Scorer | 最低 1 種 (textual_match 系) |
| COMP-00004 Trial Aggregator | n Trial 集計 |
| COMP-00010 Run Coordinator | 1 Run = 1 Model のオーケストレーション |
| COMP-00009 Result Store | Run 永続化 |
| COMP-00001 CLI Entry | `run` サブコマンドのみ |

Phase 1 では COMP-00011 (Comparator) / COMP-00012 (Report Renderer) と `compare` サブコマンドは対象外。

## 完了条件

- 上記 Component が設計仕様に沿って実装されている
- `run` サブコマンドで 1 モデル × 1 TaskProfile × n=3 Trial が完走し、Run 識別子と Run ファイルが返る (FUN-00207 観点)
- ユニットテスト: 各 Component の主要振る舞いを `tests/` 配下に追加
- 結合テスト: `run` サブコマンドが完走することを最低 1 ケース確認 (Provider はモック可)
- Python 3.13 + 標準ライブラリのみ (NFR-00302 違反なし)
- `MMDC_REQUIRED=1 bash scripts/verify.sh` が全 OK
- `pytest` または `python -m unittest` がパス
- 設計と齟齬が出た場合は実装を止めて project-master に報告 (設計を先に直す方針)

## 制約

- 過剰実装禁止 (Phase 2/3 の機能を先取りしない)
- 既存 `src/local_llm_benchmark/` 配下が空であれば新規構築可
- 外部ライブラリ追加禁止 (NFR-00302)
- OOS-00011 ほか除外要件を尊重
- 既定言語: コメント・docstring・CLI メッセージは日本語

## 検証

- ユニット/結合テスト
- `MMDC_REQUIRED=1 bash scripts/verify.sh` (mmdc 未導入なら `bash scripts/verify.sh` で代替し進捗ログに明記)

## 報告

- 追加・変更したファイルの絶対パス一覧
- 実装した Component と参照した設計 ID の対応
- テスト実行結果
- verify.sh 実行結果
- 設計と齟齬があった場合の内容と対応
- 残課題 / Phase 2 への申し送り

## 進捗ログ

- 2026-04-19 project-master: 起票
- 2026-04-19 programmer: Phase 1 実装完了。`src/local_llm_benchmark/` 配下に COMP-00001/00004/00005/00006/00007/00008/00009/00010 を新規構築。`tests/` に 33 件のユニット/結合テストを追加し全件パス。`MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 チェック OK。設計と実装の齟齬は検出されず。本 task のリンク `07-provider-adapter.md` を実ファイル名 `07-provider-contract.md` に修正。親 task (TASK-00007) の Related IDs にあった範囲表記 (ARCH 末端 ID 例示) を verify.sh 通過のため代表 ID 表記に整理。Status を `review-pending` に更新。詳細な実装一覧と検証結果は本 task に対する programmer 報告 (チャットログ) を参照。
- 2026-04-20 reviewer: 最終確認。`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、`python -m unittest discover -s tests` 33/33 OK。観点別: 設計準拠 OK (COMP-00001/00004/00005/00006/00007/00008/00009/00010 + DAT-/PVD-/SCR-/CFG-/FLW-/CLI- 系を docstring/コメントで参照)、スコープ OK (Comparator / Report Renderer / `compare` 未実装、CLI は `run` のみ)、NFR-00302 OK (`pyproject.toml` `dependencies = []`、import は標準ライブラリのみ)、テスト OK (FUN-00207 結合テスト + 失敗継続 FUN-00204 を結合層でカバー)、トレーサビリティ OK、言語 OK (コメント・CLI メッセージ日本語)。programmer による軽微修正 (リンク修正・親 task の範囲 ID 整理) は verify 通過のための実害なき技術的修正で許容範囲。Status を `done` に更新。
