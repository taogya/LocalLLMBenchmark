# TASK-00008-01 README v1.0.0 整備 + CHANGELOG 新規作成

- Status: done
- Role: docs-writer
- Parent: TASK-00008
- Related IDs: REQ-00001, NFR-00501, FUN-00207, FUN-00308, CLI-00306

## 目的

利用者が README + CHANGELOG だけで v1.0.0 のセットアップから初回 Run / Compare / Report までを最短で実演できる状態を作る。実装本体・設計書には踏み込まない (実装は確定済)。

## 一次情報 (必読)

- 既存 README: [README.md](../../README.md)
- 同梱サンプル: [configs/README.md](../../configs/README.md), `configs/task_profiles/`, `configs/model_candidates.toml`, `configs/providers.toml`, `configs/run.toml`, `configs/run-alt.toml`, `configs/comparison.toml`
- CLI 仕様: [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) (`run` / `compare` / `report` / `runs` / `comparisons` / `list` / `check`、終了コード CLI-00301..00306)
- リリース基準: [docs/development/release-criteria.md](../../docs/development/release-criteria.md)
- 実機 smoke 結果 (引用元): [progress/programmer/TASK-00007-04-manual-smoke-on-real-ollama.md](../programmer/TASK-00007-04-manual-smoke-on-real-ollama.md)

## 成果物

### 1. README.md (更新)

以下を必須セクションとして含める。既存セクションは可能な限り温存し、v1.0.0 用に追記/差し替え。

- ツールの中心目的 (REQ-00001) 1〜2 段落
- 前提環境 (Python 3.13, macOS / Linux, Ollama)
- 最短手順 (5 ステップ程度):
  1. `ollama serve` 起動 + モデル pull
  2. `pip install -e .` (または該当する導入)
  3. `local-llm-benchmark check` で設定検証
  4. `local-llm-benchmark run --run-config configs/run.toml ...` で初回 Run
  5. `compare` → `report` の流れ
- `configs/` サンプルへの導線 (`configs/README.md` を参照する旨)
- サブコマンド一覧 (簡潔表形式: `run` / `compare` / `report` / `runs` / `comparisons` / `list` / `check`)
- 既知の制約 (Provider は Ollama のみ、CLI-00306 は予約のみ等)
- リンク: CHANGELOG.md, docs/ への導線

### 2. CHANGELOG.md (新規作成、Keep a Changelog 形式)

```markdown
# Changelog

本ファイルの形式は [Keep a Changelog](https://keepachangelog.com/) に準拠する。
バージョニングは [Semantic Versioning](https://semver.org/) に準拠する。

## [1.0.0] - 2026-04-XX

### Added
- (8 Component の概要、CLI 全サブコマンド、SCR-00101..00107、Ollama Provider 等)

### Known Limitations
- Provider は Ollama のみ (REQ-00001 範囲)
- 終了コード CLI-00306 (`EXIT_COMPARISON_INCOMPLETE`) は v1.0.0 では予約のみ
- (その他あれば)
```

日付はリリース日 (本日付 or `XX` プレースホルダ + 注記)。

### 3. CLI-00306 予約注記

`docs/development/release-criteria.md` または README のいずれかに「CLI-00306 (`EXIT_COMPARISON_INCOMPLETE`) は v1.0.0 では予約のみ。実消費は次バージョン以降」を 1 行記載。配置場所は docs-writer 判断で OK。

## 完了条件

- README.md が上記内容を含み、最短手順で実機実演できる
- CHANGELOG.md が新規作成され、v1.0.0 セクションを持つ
- CLI-00306 予約注記が release-criteria.md か README に記載
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK
- 既存 docs/ の意味を変えない (利用者向け記述の追加・整理に留める)

## 制約

- 実装ファイル (`src/`) には触らない
- 設計書 (`docs/design/`, `docs/requirements/`) の意味を変えない
- 過剰な装飾を避け、簡潔に
- 言語: 日本語 (固有名詞は英語のまま)

## 報告

- 追加・変更したファイルの絶対パス一覧
- README 主要セクション一覧
- CHANGELOG v1.0.0 セクションの内容サマリ
- CLI-00306 予約注記の配置場所
- verify.sh 実行結果

## 進捗ログ

- 2026-04-20 project-master: 起票
- 2026-04-20 docs-writer: README v1.0.0 整備 / CHANGELOG.md 新規作成 / CLI-00306 予約注記を README「既知の制約」に配置 → review-pending。
  - 変更ファイル:
    - [/Users/ogasawara/develop/work/LocalLLMBenchmark/README.md](../../README.md) — 「前提環境」「最短手順 (v1.0.0)」「サブコマンド一覧」「既知の制約 (v1.0.0)」を追加。`使い方の概観 (v1)` の後に挿入し、ロードマップ等は温存。
    - [/Users/ogasawara/develop/work/LocalLLMBenchmark/CHANGELOG.md](../../CHANGELOG.md) — 新規。Keep a Changelog 形式 v1.0.0 セクション (Added / Known Limitations) のみ。日付 2026-04-20。
  - CLI-00306 予約注記の配置: README「既知の制約 (v1.0.0)」に 1 行 (release-criteria.md には既存記述があり追記不要と判断)。
  - 実機 smoke (TASK-00007-04) で使用された `local-llm-benchmark check / run / runs / compare / report` のコマンド列を最短手順に反映。
  - verify.sh 実行: 本セッションのツールセットに terminal 実行手段が含まれないためロール側で未実行。reviewer 側で `MMDC_REQUIRED=1 bash scripts/verify.sh` を再実行のうえ判定する想定 (本 task の変更は Markdown のみ・既存リンク先は実在ファイルに限定し doc-link checker を意識して作成)。
- 2026-04-20 reviewer: 8 観点を確認し合格 → done。
  - 機械チェック: `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 OK (再実行で確認)。初回は本 task ファイル先頭の「一次情報」リンク `docs/ollama/macos-setup.md` / `docs/ollama/README.md` (実在しない) で `check_doc_links` が FAIL したため、reviewer 側で当該行を削除して再パス。
  - 内容修正 (reviewer 直し):
    - [/Users/ogasawara/develop/work/LocalLLMBenchmark/CHANGELOG.md](../../CHANGELOG.md) Added 行のスコアラ名を実装/設計書 ([docs/design/08-scoring-and-ranking.md](../../docs/design/08-scoring-and-ranking.md) SCR-00101..00107) と一致させた (`contains_all` / `contains_any` / `numeric_match` / `json_field_match` → `contains` / `json_valid` / `length_within` / `numeric_close`)。利用者誤誘導の要修正点。
  - 観点判定:
    1. 最短手順: TASK-00007-04 の実機 smoke コマンド列 (`check` / `run` × 2 / `runs` / `compare --axis integrated` / `report`) と一致 → OK
    2. CHANGELOG Added/Known Limitations: スコアラ名修正後は実装範囲 (Phase 1/2/3) と一致。誇張・未実装記載なし → OK (修正後)
    3. CLI-00306 予約注記: README「既知の制約 (v1.0.0)」と CHANGELOG「Known Limitations」の双方に配置済 → OK。release-criteria.md 既存記述温存も妥当
    4. REQ-00001 中心目的: README 冒頭・CHANGELOG 冒頭で明示。誤誘導なし → OK
    5. 設計書未変更: `git status` で `docs/design/`・`docs/requirements/` に修正なしを確認 → OK
    6. 言語: 日本語+固有名詞英語 → OK
    7. リンク実在: `check_doc_links` 全 OK で担保 → OK
    8. pyproject.toml version: `1.0.0.dev0` のまま (本 task スコープ外。下記「リリース所見」参照) → 報告
  - v1.0.0 リリースに向けた最終所見 (project-master 判断材料):
    - [/Users/ogasawara/develop/work/LocalLLMBenchmark/pyproject.toml](../../pyproject.toml) `version = "1.0.0.dev0"` を `1.0.0` に確定する作業が残る。CHANGELOG 日付 `2026-04-20` と Git タグ `v1.0.0` の付与タイミングに合わせて 1 コミットでまとめると齟齬が出ない
    - 受入基準 ([docs/development/release-criteria.md](../../docs/development/release-criteria.md)) は TASK-00007-04 で全件通過済。本 task の利用者向けドキュメント整備で外向き公開条件は揃った
    - 残予約: CLI-00306 (`EXIT_COMPARISON_INCOMPLETE`) は v1.0.0 では予約のみで未消費。README/CHANGELOG/release-criteria に明記済のためリリース阻害要因ではない
