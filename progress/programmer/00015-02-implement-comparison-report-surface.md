---
request_id: "00015"
task_id: "00015-02"
parent_task_id: "00015-00"
owner: "programmer"
title: "implement-comparison-report-surface"
status: "done"
depends_on:
  - "00015-01"
created_at: "2026-04-18T23:20:00+09:00"
updated_at: "2026-04-18T18:00:30+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/report.py"
  - "tests/cli/test_main.py"
  - "docs/architecture/benchmark-foundation.md"
---

# 入力要件

- solution-architect の設計に基づき、比較レポート surface を実装したい。
- 既存 single-run report を壊さず、strict metric の意味が伝わる最小 CLI を追加したい。

# 整理した要件

- `local-llm-benchmark compare --run-dir <run_a> --run-dir <run_b> [...]` を追加し、先頭の `--run-dir` を baseline として扱う。
- 既存 `load_run_report()` と report row 正規化を再利用し、比較 key は `model_key | prompt_category | prompt_id | metric_name` に固定する。
- 既定表示は differing rows のみとし、同一 row は header の `identical_rows_omitted` へ集約する。
- duplicate path と duplicate run_id は error、suite_id mismatch は note、row 不在は `missing`、threshold 差分は `varies` で表示する。
- `json_valid_rate`、`format_valid_rate`、`constraint_pass_rate` などが strict gate であり semantic quality ではないことを compare surface と docs の両方で明示する。
- synthetic CLI test、README、architecture doc、progress をまとめて更新する。

# 作業内容

- `src/local_llm_benchmark/cli/report.py` に compare 用 dataclass、multi-run loader、baseline 差分 renderer、duplicate path / duplicate run_id validation、`missing` と `threshold=varies` 表示を追加した。
- `src/local_llm_benchmark/cli/main.py` に `compare` subcommand と handler を追加し、既存 `report` とは分離した入口にした。
- `tests/cli/test_main.py` に compare help、差分表示、同一 row の既定省略、missing row、suite mismatch note、threshold varies、duplicate error、strict gate note の synthetic test を追加した。
- `README.md` に compare の最小実行例、baseline の扱い、differing rows 既定、`missing` の意味、strict gate の注意書きを追加した。
- `docs/architecture/benchmark-foundation.md` に multi-run compare CLI の設計意図、row key、表示方針、strict gate 解釈を追記した。
- 診断で出た行長違反を `src/local_llm_benchmark/cli/main.py`、`src/local_llm_benchmark/cli/report.py`、`tests/cli/test_main.py` で最小修正した。

# 判断

- compare は既存 `report` の option 拡張ではなく、新しい `compare` subcommand として分離した。single-run summary と multi-run diff の責務を混ぜないためである。
- 比較ロジックは artifact schema を変えず、single-run loader の再利用だけで構成した。これにより保存形式や provider 実装へ影響を広げていない。
- row の同一判定は value だけでなく threshold、passed、sample_count、row 有無を含めた state で行い、運用 gate 差分を落とさないようにした。
- strict gate の注意書きは compare header に常時表示し、semantic quality との差を docs 側にも重ねて書く方針にした。

# 成果

## 変更したファイル

- `src/local_llm_benchmark/cli/main.py`
- `src/local_llm_benchmark/cli/report.py`
- `tests/cli/test_main.py`
- `README.md`
- `docs/architecture/benchmark-foundation.md`

## 実装内容

- 保存済み run を baseline 差分で比較できる `compare` CLI を追加した。
- compare 出力は `model_key | prompt_category | prompt_id | metric_name` ごとに差分だけを表示し、同一 row は件数だけ残す最小 surface にした。
- `missing`、`threshold=varies`、duplicate path / run_id error、suite mismatch note、strict gate note まで含めて表示契約を固定した。
- single-run `report` の既存挙動は維持し、storage schema と provider 実装には手を入れていない。

## 検証内容

- `get_errors` で `src/local_llm_benchmark/cli/main.py`、`src/local_llm_benchmark/cli/report.py`、`tests/cli/test_main.py` の診断 0 件を確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_main tests.cli.test_live_smoke`
  - 22 tests, OK, skipped=3
  - compare の synthetic CLI test と既存 live smoke の通常 skip 経路が通ることを確認した。

# 次アクション

- reviewer が compare の row 同一判定、strict gate note、README / architecture doc の記述整合を確認する。

# リスク

- compare は text surface のみで、JSON 出力や filter はまだないため機械処理には向かない。
- suite_id mismatch は note 扱いで比較自体は継続するため、suite / plan 差分が大きい run 同士でも row key が一致すれば表示される。

# 改善提案

- compare 用の保存済み artifact fixture を増やし、3 run 以上や multi-case の組み合わせも golden に近い形で固定すると将来の表示崩れを検知しやすい。
- 自動集計や外部レポート連携が必要になった段階で、`compare --format json` のような機械向け出力を別 request で検討するとよい。