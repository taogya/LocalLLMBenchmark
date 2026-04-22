---
request_id: "00015"
task_id: "00015-03"
parent_task_id: "00015-00"
owner: "reviewer"
title: "review-comparison-report-surface"
status: "done"
depends_on:
  - "00015-01"
  - "00015-02"
created_at: "2026-04-18T23:20:00+09:00"
updated_at: "2026-04-18T18:04:11+09:00"
related_paths:
  - "progress/project-master/00015-00-implement-comparison-report-surface.md"
  - "progress/solution-architect/00015-01-design-comparison-report-surface.md"
  - "progress/programmer/00015-02-implement-comparison-report-surface.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/report.py"
  - "tests/cli/test_main.py"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
---

# 入力要件

- 比較レポート surface の設計・実装が benchmark の目的と strict metric の解釈に整合するか確認したい。

# 作業内容

- progress/solution-architect/00015-01-design-comparison-report-surface.md と progress/programmer/00015-02-implement-comparison-report-surface.md を読み、compare の最小 CLI 形状、strict gate の説明方針、例外条件の扱いを実装と照合した。
- src/local_llm_benchmark/cli/main.py、src/local_llm_benchmark/cli/report.py、tests/cli/test_main.py、README.md、docs/architecture/benchmark-foundation.md を確認し、single-run report と compare の責務分離、strict gate note、docs の整合性を点検した。
- compare 出力の strict gate note が metric 名を直接含まず、README / architecture doc より一段抽象的だったため、json_valid_rate / format_valid_rate / constraint_pass_rate を明示する軽微修正を src/local_llm_benchmark/cli/report.py と tests/cli/test_main.py に反映した。
- source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_main tests.cli.test_live_smoke を再実行し、22 tests, OK, skipped=3 を確認した。

# 判断

- compare は新しい subcommand として分離されており、single-run report の stable 入口を崩していない。artifact loader は load_run_report() を共用しつつ、render_run_report() と render_comparison_report() の責務は分かれている。
- compare の CLI 形状は repeatable な --run-dir で baseline を明示し、differing rows のみを既定表示する最小スライスとして妥当である。model 集計や自動探索を持ち込んでおらず、surface の広がり方も制御できている。
- strict gate note は README と architecture doc に加えて compare 出力自体でも metric 名を明示するように補強したため、json_valid_rate / format_valid_rate / constraint_pass_rate を semantic quality 指標と誤読しにくい状態になった。
- duplicate path は error、duplicate run_id は error、suite_id mismatch は note、missing は row 不在表示と note、threshold 差分は threshold=varies という扱いで、設計・実装・tests の 3 点が一致している。
- OpenAI-compatible provenance と strict / tolerant split への拡張余地は、row key を provider 非依存に保ち、metric_name を opaque に扱う設計で維持されている。現時点で責務境界を崩す兆候は見当たらない。

# 成果

## 確認対象

- progress/solution-architect/00015-01-design-comparison-report-surface.md
- progress/programmer/00015-02-implement-comparison-report-surface.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/cli/report.py
- tests/cli/test_main.py
- README.md
- docs/architecture/benchmark-foundation.md

## 発見事項

- 解消済み軽微事項: compare 出力の strict gate note が metric 名を直接含まず、README / architecture doc より抽象度が高かったため、json_valid_rate / format_valid_rate / constraint_pass_rate を明示する最小修正を reviewer 側で反映した。
- 未解消の重大 finding はなし。

## 残課題

- compare は text surface のみで、機械向け JSON 出力や label 付けはまだない。
- suite_id mismatch は note 扱いで比較を継続するため、plan 差分が大きい run 同士でも row_key が一致すれば表示される。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、strict gate 誤読防止の軽微事項も reviewer 側で解消済みである。

## 改善提案

- OpenAI-compatible 比較が増えた段階で、compare header に provider_id または config_root 由来の短い descriptor を追加すると provenance を読み取りやすい。
- 後続 request で strict / tolerant split を入れる場合は、既存 strict metric を上書きせず metric_name を分けて並列表示する方が compare の解釈を保ちやすい。

# 検証

- source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_main tests.cli.test_live_smoke
  - 22 tests, OK, skipped=3

# 次アクション

- project-master へ、重大 finding なし、strict gate note の軽微補強を reviewer 側で解消済み、compare の CLI / docs / tests は整合している、という結果を引き継ぐ。