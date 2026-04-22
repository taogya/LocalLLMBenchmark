---
request_id: "00011"
task_id: "00011-03"
parent_task_id: "00011-00"
owner: "reviewer"
title: "review-run-metrics-report-surface"
status: "done"
depends_on:
  - "00011-02"
created_at: "2026-04-18T15:15:00+09:00"
updated_at: "2026-04-18T18:55:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/report.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_live_smoke.py"
---

# 入力要件

- run-metrics の利用面が report 準備として十分か確認したい。

# 整理した要件

- 出力粒度、docs、tests、用語整合を確認する。
- `report --run-dir` の自然さ、threshold / passed / n の誤読余地、`record_count` と `sample_count` の説明、README / docs 導線、最小回帰 test を横断確認する。

# 作業内容

- README.md、docs/architecture/benchmark-foundation.md、src/local_llm_benchmark/cli/main.py、src/local_llm_benchmark/cli/report.py、tests/cli/test_main.py、tests/cli/test_live_smoke.py を確認し、`report` subcommand の入口、表示列、用語、README / docs 導線、synthetic test と live smoke のカバレッジを照合した。
- progress/solution-architect/00011-01-design-run-metrics-report-surface.md と progress/programmer/00011-02-implement-run-metrics-report-surface.md を読み、設計意図と実装差分を確認した。
- 軽微な整合修正として、`src/local_llm_benchmark/cli/report.py` の legend に `records=manifest.record_count` を明示し、`manifest.json` と `run-metrics.json` の `run_id` 不一致を検出する validation を追加した。あわせて `tests/cli/test_main.py` に回帰 test を追加した。
- `source .venv/bin/activate && python -m unittest tests.cli.test_main tests.cli.test_live_smoke` を再実行し、review 時点で 14 tests, OK, skipped=3 を確認した。

# 判断

- `local-llm-benchmark report --run-dir <run_dir>` は、直前の `run` summary が `result_dir` を出すこと、README が `suites -> run -> report` の順で導くことから、最小利用面として自然である。
- 出力は header 5 行、legend 1 行、metric row 群に限定されており、single-run の確認用途としては情報過多ではない。scorer 名や aggregation を既定表示から外している点も妥当である。
- `threshold` の `-` / `>=1.0` / `80-120 chars`、`passed` の `pass` / `fail` / `n/a`、`n=sample_count` の表現は synthetic test で固定されており、range threshold を run gate と誤読しない `passed=n/a` も一貫している。
- `record_count` と `sample_count` の意味差は README と architecture doc に記載があり、CLI 側も今回の修正で legend に `records=manifest.record_count` を出すため、最小利用面としての説明不足は解消できた。
- `report` helper は presence / type validation に加えて artifact 間の `run_id` 整合も確認するようになり、single-run report としての安定性が上がった。
- tests は synthetic CLI test で help、成功表示、threshold / passed 整形、欠落 artifact、`run_id` 不一致 error、scope mismatch note を押さえ、live smoke では opt-in 条件を維持したまま `run -> report` の成功経路を確認しているため、最小回帰として十分である。

# 成果

## 確認対象

- README.md
- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/cli/report.py
- tests/cli/test_main.py
- tests/cli/test_live_smoke.py

## 発見事項

- 解消済み軽微事項: `src/local_llm_benchmark/cli/report.py` の legend が `records` の意味を明示しておらず、`record_count` と `sample_count` の違いが CLI 単体では少し読み取りにくかったため、`records=manifest.record_count` を追加した。
- 解消済み軽微事項: `src/local_llm_benchmark/cli/report.py` が `manifest.json` と `run-metrics.json` の `run_id` 一致を検証しておらず、壊れた run_dir を誤って single-run report として表示しうる状態だったため、一致確認と回帰 test を追加した。
- 未解消の重大 finding はなし。

## 残課題

- live smoke は `report` の成功経路までは確認しているが、実 run artifact に対する threshold / note の全 variation は synthetic test 側に依存している。
- 将来 1 prompt_id あたり複数 case を集約するようになった場合、scope mismatch note の文言は `sample_count` と scope 集約の関係をもう一段明示した方がよい可能性がある。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、軽微な整合差は reviewer 側で解消済みである。

## 改善提案

- 比較レポート本体へ進む段階で、single-run report の row 正規化 helper を shared loader として切り出すと multi-run 側へ再利用しやすい。
- multi-case prompt を入れる段階では、`records`、scope、`n` の関係を CLI note と docs の両方で 1 回見直すと誤読を防ぎやすい。

# 検証

- `source .venv/bin/activate && python -m unittest tests.cli.test_main tests.cli.test_live_smoke`
  - 14 tests, OK, skipped=3

# 次アクション

- project-master へ、重大 finding なし、軽微な整合修正 2 件を reviewer 側で解消済み、関連 CLI tests 再実行成功という結果を引き継ぐ。

# 関連パス

- README.md
- src/local_llm_benchmark/cli
- tests/cli
- tests/storage