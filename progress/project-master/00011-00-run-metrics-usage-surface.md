---
request_id: "00011"
task_id: "00011-00"
parent_task_id:
owner: "project-master"
title: "run-metrics-usage-surface"
status: "done"
depends_on: []
child_task_ids:
  - "00011-01"
  - "00011-02"
  - "00011-03"
created_at: "2026-04-18T15:15:00+09:00"
updated_at: "2026-04-18T19:05:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/cli"
  - "src/local_llm_benchmark/benchmark"
  - "src/local_llm_benchmark/storage"
  - "tests/cli"
---

# 入力要件

- OpenAI-compatible provider は live 検証なし前提で進めてよい。
- 次に、比較レポート整備へ進む準備として run-metrics の利用面を固めたい。

# 整理した要件

- run-metrics.json は保存済みだが、現在は user-facing な利用導線が弱い。
- 比較レポート本体の前段として、run-metrics を安定して読み、要約できる利用面を追加する。
- 情報過多は避けつつ、比較に必要な metric を確認できる導線にする。

# 作業内容

- 現状の run-metrics 実装、runner、storage、README、review 記録を確認し、保存はできている一方、利用面は JSON artifact 止まりであることを確認した。
- 比較レポート整備の前段として、run directory を受けて run-metrics を要約表示する report CLI を最小候補に採用した。
- 設計、実装、レビューの 3 子タスクへ分けて進める。
- 設計アーキテクトが、`local-llm-benchmark report --run-dir <run_dir>` を最小 CLI とし、single-run の metric 要約、threshold 整形、`record_count` と `sample_count` の意味差、比較レポート本体への接続方針を整理した。
- programmer が `src/local_llm_benchmark/cli/report.py` を追加し、report subcommand、README / architecture docs の導線、synthetic CLI test と live smoke 側の report 呼び出しを実装した。
- reviewer が `records=manifest.record_count` の legend 明示と `manifest.json` / `run-metrics.json` の `run_id` 一致検証を追加し、CLI tests 再実行で重大 findings なしを確認した。

# 判断

- ここで重要なのは新しい評価指標ではなく、既存 run-metrics の意味と使い方を固定すること。
- 最小の利用面は、run-metrics.json と manifest.json を読む CLI 要約と、その出力を固定するテスト・docs である。
- 比較レポート本体へ進む前に single-run の user-facing な利用面を置くことで、artifact schema の変更検知と用語整合を先に固められる。

# 成果

- request_id 00011 の親記録を作成した。
- `local-llm-benchmark report --run-dir <run_dir>` を追加し、保存済み single-run の metric 要約を CLI から確認できるようにした。
- report 出力は `run_id`、`suite_id`、`run_dir`、`records`、`metric_rows` と、各 metric row の `scope=model_key | prompt_category | prompt_id`、`metric_name`、`value`、`threshold`、`passed`、`n` を固定した。
- `records` は manifest の `record_count`、`n` は run-metrics の `sample_count` であることを README、architecture docs、CLI legend に明示した。
- `threshold` の `null -> -`、`min -> >=1.0`、`range -> 80-120 chars` 整形と、`passed` の `pass / fail / n/a` 表示を固定した。
- `manifest.json` と `run-metrics.json` の `run_id` 不一致を report CLI が検出するようにした。
- 関連検証として reviewer 再実行時点で `python -m unittest tests.cli.test_main tests.cli.test_live_smoke` は 14 tests, OK, skipped=3、diagnostics 0 件である。

# 次アクション

- 設計アーキテクトへ、run-metrics 利用面の最小 CLI と表示粒度を委譲する。
- programmer へ、report CLI と tests / docs 更新を委譲する。
- reviewer へ、利用面が過不足なく固まっているかを確認してもらう。
- 比較レポート本体へ進む段階では、single-run report の row 正規化 helper を shared loader として切り出し、multi-run 比較へ再利用する。
- multi-case prompt を導入する段階では、scope と `n` と `records` の関係を report note と docs で再調整する。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/cli
- src/local_llm_benchmark/benchmark
- src/local_llm_benchmark/storage
- tests/cli