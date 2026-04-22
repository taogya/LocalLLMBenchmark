---
request_id: "00015"
task_id: "00015-00"
parent_task_id:
owner: "project-master"
title: "implement-comparison-report-surface"
status: "done"
depends_on: []
child_task_ids:
  - "00015-01"
  - "00015-02"
  - "00015-03"
created_at: "2026-04-18T23:20:00+09:00"
updated_at: "2026-04-18T23:30:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli/report.py"
  - "src/local_llm_benchmark/cli"
  - "tests/cli/test_main.py"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/project-master/00011-00-run-metrics-usage-surface.md"
  - "progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md"
  - "progress/solution-architect/00015-01-design-comparison-report-surface.md"
  - "progress/programmer/00015-02-implement-comparison-report-surface.md"
  - "progress/reviewer/00015-03-review-comparison-report-surface.md"
---

# 入力要件

- 残っているロードマップがあるなら進めたい。
- 現在の strict metric の意味を崩さず、保存済み結果から比較しやすい利用面を先に整えたい。

# 整理した要件

- 必須要件は、README の未完了主項目である比較レポート整備を request 化すること。
- 必須要件は、既存 single-run report を土台に multi-run 比較へ進める最小スライスを定義し、設計・実装・レビューへ委譲すること。
- 必須要件は、strict metric を semantic quality と誤読しにくい表示にすること。
- 任意要件は、OpenAI-compatible suite / smoke や strict/tolerant split の将来接続を阻害しない shape にすること。

# 作業内容

- request 00011 の single-run report helper、README のロードマップ、request 00014 の評価妥当性整理を確認し、次の主タスクを比較レポート整備と判断した。
- 比較レポート surface の最小設計を solution-architect へ、実装を programmer へ、最終確認を reviewer へ委譲する。
- solution-architect は、新規 `compare` subcommand、repeatable な `--run-dir`、先頭 run を baseline とする差分表示、differing rows 既定表示、strict gate note を最小境界として整理した。
- programmer は compare CLI を実装し、single-run loader を再利用した multi-run 差分表示、duplicate error、suite mismatch note、missing / threshold varies 表示、README / architecture doc / tests 更新まで完了した。
- reviewer は重大 finding なしと判断し、compare の strict gate note が抽象的すぎた軽微事項だけを修正し、`json_valid_rate`、`format_valid_rate`、`constraint_pass_rate` を直接明示する形へ補強した。

# 判断

- 次に進めるべき主タスクは multi-run 比較 surface である。
- 表示面では、strict gate を比較していることが分かる legend や note が必要である。
- OpenAI-compatible suite / smoke はこの後の provider-neutral 拡張として扱う。
- compare は `report` の拡張ではなく独立 subcommand として分離する方が、single-run summary と multi-run diff の責務を混ぜずに済む。
- 比較単位は `model_key | prompt_category | prompt_id | metric_name` に固定し、provider 固有情報は row key へ持ち込まない方が拡張余地を保ちやすい。
- strict gate の注意書きは compare 出力自体、README、architecture doc の 3 面でそろえるのが妥当である。

# 成果

- request 00015 の親記録を作成した。
- `local-llm-benchmark compare --run-dir <run_a> --run-dir <run_b> [...]` を追加し、先頭 run を baseline にした multi-run 差分表示を行えるようにした。
- compare は differing rows だけを既定表示し、identical rows は header 件数へ集約する最小 surface とした。
- duplicate path / duplicate run_id は error、suite mismatch は note、missing row と threshold differs は可視化に留める表示契約を固定した。
- strict gate note を compare 出力、README、architecture doc へ反映し、`json_valid_rate`、`format_valid_rate`、`constraint_pass_rate` などを semantic quality と誤読しにくい状態にした。
- 検証として、関連 Python 診断 0 件、`python -m unittest tests.cli.test_main tests.cli.test_live_smoke` で 22 tests, OK, skipped=3 を確認した。

# 次アクション

- 次の優先度は OpenAI-compatible model を含む最小 suite か opt-in smoke の追加である。
- strict / tolerant split は compare 上の解釈を保ったまま、別 request で metric 分離として扱う。

# 関連パス

- README.md
- src/local_llm_benchmark/cli/report.py
- tests/cli/test_main.py