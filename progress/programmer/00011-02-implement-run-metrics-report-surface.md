---
request_id: "00011"
task_id: "00011-02"
parent_task_id: "00011-00"
owner: "programmer"
title: "implement-run-metrics-report-surface"
status: "done"
depends_on:
  - "00011-01"
created_at: "2026-04-18T15:15:00+09:00"
updated_at: "2026-04-18T09:05:43+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli"
  - "src/local_llm_benchmark/cli/report.py"
  - "tests/cli"
  - "docs/architecture/benchmark-foundation.md"
---

# 入力要件

- run-metrics の利用面を実装したい。

# 整理した要件

- `local-llm-benchmark report --run-dir <run_dir>` を追加し、`manifest.json` と `run-metrics.json` から single-run の metric 要約を表示する。
- row は `model_key | prompt_category | prompt_id | metric_name | value | threshold | passed | n` を最小表示にし、`value`、`threshold`、`passed` の整形を固定する。
- `record_count` と `sample_count` の意味差を legend / note で明示し、欠落 artifact error、synthetic CLI test、live smoke、README、architecture doc まで更新する。

# 作業内容

- `src/local_llm_benchmark/cli/report.py` を追加し、`manifest.json` と `run-metrics.json` の読み出し、最小検証、row 正規化、single-run report 表示を実装した。
- `src/local_llm_benchmark/cli/main.py` に `report` subcommand を追加し、`--run-dir` から保存済み run を読めるようにした。
- `tests/cli/test_main.py` に report help、synthetic run_dir の成功表示、threshold / passed 整形、欠落 artifact error、scope mismatch note の回帰 test を追加した。
- `tests/cli/test_live_smoke.py` で `run` 後に `report` を呼び、`run_id`、`suite_id`、既知 metric 名、`n=1` が出ることを固定した。
- `README.md` と `docs/architecture/benchmark-foundation.md` を最小更新し、`suites -> run -> report` の導線と `record_count` / `sample_count` / `threshold` の意味差を追記した。

# 判断

- JSON schema は変更せず、CLI helper 側だけで `manifest` と `run-metrics` を読み合わせる方針を維持した。
- report の責務は single-run の stable な読み出しと最小表示に留め、比較レポート本体で再利用しやすい row 正規化だけを helper に閉じ込めた。
- `record_count` と `sample_count` の意味差は常時 legend に出しつつ、実際に差分が出たときだけ note を追加する実装にした。

# 成果

- 保存済み run から metric 要約を確認できる `report` CLI が追加された。
- run-metrics の `threshold` / `passed` / `sample_count` の見せ方が docs と tests まで含めて固定された。
- live smoke でも `suites -> run -> report` の最小導線を確認できる状態になった。

# 次アクション

- reviewer が command 名、row 表示、range threshold の `passed=n/a`、`record_count` と `sample_count` の意味差を横断確認する。
- 次段階の比較レポート整備では、この helper の row 正規化を multi-run 集計へ再利用する。

# 関連パス

- README.md
- src/local_llm_benchmark/cli
- tests/cli
- tests/storage