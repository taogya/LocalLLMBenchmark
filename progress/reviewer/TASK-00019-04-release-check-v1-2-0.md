# TASK-00019-04 v1.2.0 リリース前チェック

- Status: done
- Role: reviewer
- Parent: TASK-00019
- Related IDs: REQ-00001, NFR-00001, NFR-00302, NFR-00501, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408, FUN-00409, FUN-00410, PROG-00103
- 起票日: 2026-04-24

## 目的

v1.2.0 リリース前に、README / CHANGELOG / release-criteria / package version の整合と、必要な verify / test / smoke 観点を横断確認する。release 日付 2026-04-24 の記載整合もこの task で最終確認する。

## 完了条件

- 着手時点で TASK-00019-01 / 02 / 03 が `review-pending` または `done` になっている。
- README / CHANGELOG / `docs/development/release-criteria.md` / `pyproject.toml` / user-facing version 表記が相互に整合している。
- `MMDC_REQUIRED=1 bash scripts/verify.sh` が全 OK。
- 変更対象に応じた focused test / smoke が実施され、release blocker の有無が明記されている。

## スコープ外

- 新機能追加
- Git tag / GitHub Release 作成

## 進捗ログ

- 2026-04-24 project-master: 起票。release docs と version 反映がそろった時点で横断確認を依頼する。
- 2026-04-24 reviewer: TASK-00019-01 / 02 / 03 が review-pending であることを確認し、README / CHANGELOG / release-criteria / pyproject / CLI source を横断確認した。README の `最短手順` / `既知の制約` 見出し整理、CHANGELOG 1.2.0 節、release-criteria の v1.2.0 化、`pyproject.toml` / CLI help / package docstring の 1.2.0 表記は整合している。一方で `MMDC_REQUIRED=1 bash scripts/verify.sh` は `progress/solution-architect/TASK-00019-02-update-release-criteria-v1-2-0.md` の active task に OOS- が残っているため FAIL、加えて packaging metadata として残っている `src/local_llm_benchmark.egg-info/PKG-INFO` は Version / Summary とも 1.0.0 のままで、release artifact 上の version 整合をこの環境では完了確認できなかった。`tests/test_cli_phase3.py` は 31 tests 成功、`PYTHONPATH=src python -m local_llm_benchmark.cli.main --help` と package docstring は v1.2.0 を確認。blocker ありのため Status を `review-pending` に更新した。
- 2026-04-24 reviewer: focused recheck を実施。`progress/solution-architect/TASK-00019-02-update-release-criteria-v1-2-0.md` の `Related IDs:` から OOS- が除去されていること、`src/local_llm_benchmark.egg-info/PKG-INFO` の `Version` / `Summary` が 1.2.0 に同期されていることを確認した。`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10 checks すべて OK、`pyproject.toml` / `src/local_llm_benchmark.egg-info/PKG-INFO` / `src/local_llm_benchmark/__init__.py` の version 表記も 1.2.0 で整合したため、前回 blocker 2 件は解消と判定し Status を `done` に更新した。なお progress ルール上、親 TASK-00019 を `done` に進めるには子 task 01 / 02 / 03 が `done` へ遷移している必要がある。

## レビュー記録 (reviewer 用)

### 判定

- done (focused recheck で前回 blocker 2 件の解消を確認)

### verify.sh 実行結果サマリ

- OK: check_id_format.py
- OK: check_id_uniqueness.py
- OK: check_id_references.py
- OK: check_doc_links.py
- OK: check_progress_format.py
- OK: check_mermaid_syntax.py
- OK: check_markdown_syntax.py
- OK: check_no_implementation_leak.py
- OK: check_role_boundary.py
- OK: check_oos_no_implementation.py

### テスト / コマンド結果サマリ

- OK: `MMDC_REQUIRED=1 bash scripts/verify.sh` は 10 checks すべて OK
- OK: `pyproject.toml` の `project.version = "1.2.0"` と `description = "ローカル LLM ベンチマーク本体 (v1.2.0)"` を確認
- OK: `src/local_llm_benchmark.egg-info/PKG-INFO` の `Version: 1.2.0` / `Summary: ローカル LLM ベンチマーク本体 (v1.2.0)` を確認
- OK: `src/local_llm_benchmark/__init__.py` の package docstring が `v1.2.0 最小垂直スライス。詳細は各サブモジュールの docstring 参照。` であることを確認
- OK: 前回レビュー済みの README / CHANGELOG / release-criteria / CLI help に関する判定を維持し、今回の focused recheck では blocker 2 件の解消確認に限定した

### 確認対象

- progress/project-master/TASK-00019-v1-2-0-release-prep.md
- progress/docs-writer/TASK-00019-01-readme-changelog-v1-2-0.md
- progress/solution-architect/TASK-00019-02-update-release-criteria-v1-2-0.md
- progress/programmer/TASK-00019-03-bump-version-v1-2-0.md
- pyproject.toml
- src/local_llm_benchmark/__init__.py
- src/local_llm_benchmark.egg-info/PKG-INFO

### 発見事項

- 解消: [progress/solution-architect/TASK-00019-02-update-release-criteria-v1-2-0.md](../../progress/solution-architect/TASK-00019-02-update-release-criteria-v1-2-0.md) の `Related IDs:` から OOS- が除去され、`MMDC_REQUIRED=1 bash scripts/verify.sh` の `check_oos_no_implementation.py` も OK に戻った。
- 解消: [src/local_llm_benchmark.egg-info/PKG-INFO](../../src/local_llm_benchmark.egg-info/PKG-INFO) の `Version` / `Summary` は 1.2.0 に同期され、[pyproject.toml](../../pyproject.toml) と [src/local_llm_benchmark/__init__.py](../../src/local_llm_benchmark/__init__.py) の version 表記と整合した。
- 進行管理: 技術的な release blocker は解消したが、[progress/project-master/TASK-00019-v1-2-0-release-prep.md](../../progress/project-master/TASK-00019-v1-2-0-release-prep.md) を `done` に進めるには progress ルール上、子 task 01 / 02 / 03 が `done` または `cancelled` である必要がある。現時点では 3 件とも `review-pending` のため、親 task の `done` 化はまだ不可。
- 合格: README / CHANGELOG / release-criteria / CLI help に関する前回レビュー結果を維持できることを、今回の focused recheck の前提として扱って差し支えない。

### 直接修正した範囲

- 本 reviewer task の Status、進捗ログ、レビュー記録を更新

### 差し戻し事項

- なし。focused recheck の対象だった前回 blocker 2 件は解消済み。

### ユーザー報告可否

- 可。focused recheck の対象だった前回 blocker 2 件は解消し、reviewer 観点の release blocker は現時点で無い。ただし progress ルール上、親 TASK-00019 を `done` に進めるのは、TASK-00019-01 / 02 / 03 が各担当ロールによって `done` へ更新された後である。