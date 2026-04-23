# TASK-00019-03 package version 1.2.0 反映

- Status: done
- Role: programmer
- Parent: TASK-00019
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-24

## 目的

release artifact 上の version 表記を 1.2.0 に更新する。`pyproject.toml` に残る `1.0.0` と、CLI help や package docstring に残る v1.0.0 表記を、v1.2.0 リリースに合わせて整合させる。

## 完了条件

- `pyproject.toml` の package version が `1.2.0` になっている。
- user-facing な version 表記 (CLI help など) が 1.2.0 と矛盾しない。
- 変更に対する focused validation が実施され、結果が進捗ログに記録されている。

## スコープ外

- README / CHANGELOG 更新 (TASK-00019-01)
- release-criteria 更新 (TASK-00019-02)
- Git tag 作成

## 進捗ログ

- 2026-04-24 project-master: 起票。`pyproject.toml` は `version = "1.0.0"`、`description` も v1.0.0 のままであり、[src/local_llm_benchmark/cli/main.py](../../src/local_llm_benchmark/cli/main.py) と [src/local_llm_benchmark/__init__.py](../../src/local_llm_benchmark/__init__.py) にも v1.0.0 表記が残っていることを確認した。
- 2026-04-24 programmer: [progress/project-master/TASK-00019-v1-2-0-release-prep.md](../../progress/project-master/TASK-00019-v1-2-0-release-prep.md) と本 task の完了条件を確認し、scope を package version と既存 user-facing version 表記の整合に限定して着手した。README / CHANGELOG / docs は本 task では変更しない方針を再確認した。
- 2026-04-24 programmer: [pyproject.toml](../../pyproject.toml), [src/local_llm_benchmark/cli/main.py](../../src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/__init__.py](../../src/local_llm_benchmark/__init__.py) を最小更新し、package version を `1.2.0`、package description を `ローカル LLM ベンチマーク本体 (v1.2.0)` に更新した。あわせて CLI help の description と package docstring の v1.0.0 表記を v1.2.0 にそろえ、source module header へ TASK-00019-03 を追記した。機能追加や public surface の変更は行っていない。
- 2026-04-24 programmer: focused validation を実施。touched files に対する `get_errors` は [pyproject.toml](../../pyproject.toml), [src/local_llm_benchmark/cli/main.py](../../src/local_llm_benchmark/cli/main.py), [src/local_llm_benchmark/__init__.py](../../src/local_llm_benchmark/__init__.py) のすべてで問題なし。`PYTHONPATH=src python -m local_llm_benchmark.cli.main --help | head -n 8` では help 冒頭に `ローカル LLM ベンチマーク本体 (v1.2.0)。` が表示され、`PYTHONPATH=src python -c "import local_llm_benchmark; print(local_llm_benchmark.__doc__.splitlines()[2])"` では `v1.2.0 最小垂直スライス。詳細は各サブモジュールの docstring 参照。` を確認した。完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-24 programmer: reviewer 差し戻し対応として、source tree に残っていた packaging metadata [src/local_llm_benchmark.egg-info/PKG-INFO](../../src/local_llm_benchmark.egg-info/PKG-INFO) を [pyproject.toml](../../pyproject.toml) と現行 [README.md](../../README.md) に手動同期した。`Version` / `Summary` を `1.2.0` に更新し、PKG-INFO 内の stale な `最短手順 (v1.0.0)` / `既知の制約 (v1.0.0)` と旧 CLI 導線を現行の v1.2.0 公開面へ置換した。`src/local_llm_benchmark.egg-info/` 配下の version 表記は確認し、該当は PKG-INFO のみだった。環境に `setuptools` が無く fresh artifact の自動再生成はできないため、本差し戻しでは source tree metadata の整合回復に限定した。
- 2026-04-24 programmer: 差し戻し修正後の focused validation を実施。`get_errors` で [src/local_llm_benchmark.egg-info/PKG-INFO](../../src/local_llm_benchmark.egg-info/PKG-INFO) に問題がないことを確認し、`grep_search` で `src/local_llm_benchmark.egg-info/**` を再確認した結果、`Version: 1.2.0` / `Summary: ローカル LLM ベンチマーク本体 (v1.2.0)` へ更新済みであること、`1.0.0` の残存は roadmap 上の履歴参照 (`### v1.0.0`) のみで stale metadata ではないことを確認した。reviewer の再確認待ちとして Status は `review-pending` を維持する。
- 2026-04-24 programmer: [progress/reviewer/TASK-00019-04-release-check-v1-2-0.md](../../progress/reviewer/TASK-00019-04-release-check-v1-2-0.md) が `done` / 合格になったことを反映した。reviewer が指摘していた release blocker 2 件の解消確認と focused recheck 完了を受け、本 task の完了条件は満たされたものとして Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- reviewer 重点確認: [pyproject.toml](../../pyproject.toml) の package metadata、[src/local_llm_benchmark/cli/main.py](../../src/local_llm_benchmark/cli/main.py) の help description、[src/local_llm_benchmark/__init__.py](../../src/local_llm_benchmark/__init__.py) の package docstring がすべて 1.2.0 で整合していること。
- reviewer 重点確認: [src/local_llm_benchmark.egg-info/PKG-INFO](../../src/local_llm_benchmark.egg-info/PKG-INFO) の `Version` / `Summary` と README 由来の公開面説明が、[pyproject.toml](../../pyproject.toml) の 1.2.0 および現行 [README.md](../../README.md) と矛盾しないこと。
- reviewer 重点確認: 本 task が README / CHANGELOG / docs を触らず、release artifact 上の version 整合だけに変更を限定していること。