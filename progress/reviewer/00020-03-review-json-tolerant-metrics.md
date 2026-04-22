---
request_id: "00020"
task_id: "00020-03"
parent_task_id: "00020-00"
owner: "reviewer"
title: "review-json-tolerant-metrics"
status: "done"
depends_on:
  - "00020-02"
created_at: "2026-04-19T14:10:00+09:00"
updated_at: "2026-04-19T13:33:27+09:00"
related_paths:
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/benchmark/test_evaluation.py"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/programmer/00020-02-implement-json-tolerant-metrics.md"
---

# 要件整理

- strict gate の既存意味を壊さずに tolerant JSON metric が追加されているか確認する。
- metric 名、README、architecture doc の説明が誤読を増やしていないか確認する。
- 追加 test が変更の主経路を十分に押さえているか確認する。

# 作業内容

- progress/evaluation-analyst/00020-01-verify-live-run-and-scope-json-split.md と progress/programmer/00020-02-implement-json-tolerant-metrics.md を読み、strict metric の維持条件、payload metric の意図、非スコープを確認した。
- src/local_llm_benchmark/benchmark/evaluation.py を確認し、strict row と payload row が別 metric 名で追加されていること、strict / payload scorer の入口が分離されていること、payload 前処理 helper が前後空白除去とレスポンス全体が単一 fenced block のときだけ unwrap する実装であることを確認した。
- tests/benchmark/test_evaluation.py を確認し、bare JSON 正常系、single fenced JSON の strict fail / payload pass 分離、前後 prose 混在 fail、aggregate_run_metrics への payload row 反映が追加されていることを確認した。
- README.md と docs/architecture/benchmark-foundation.md を確認し、strict gate の意味、payload diagnostic の位置づけ、前処理上限、strict fail を上書きしないことが実装と同じ粒度で説明されていることを確認した。
- get_errors で src/local_llm_benchmark/benchmark/evaluation.py、tests/benchmark/test_evaluation.py、README.md、docs/architecture/benchmark-foundation.md の diagnostics 0 件を確認した。
- source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.benchmark.test_evaluation を実行し、5 tests, OK を確認した。
- source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.benchmark.test_runner tests.benchmark.test_evaluation を実行し、7 tests, OK を確認した。

# 判断

## 1. strict metric 名、threshold、意味の維持

- 妥当である。extraction の exact_match_rate と json_valid_rate、constrained_generation の constraint_pass_rate と format_valid_rate は既存の metric 名を維持しており、json_valid_rate >= 1.0 と format_valid_rate >= 1.0 の threshold も変更されていない。
- payload 系は json_payload_valid_rate、payload_exact_match_rate、payload_format_valid_rate、payload_constraint_pass_rate として別 metric 名で追加されており、strict row の意味を上書きしていない。

## 2. payload metric が strict fail を上書きしない設計か

- 妥当である。evaluation.py では strict scorer と payload scorer が別の scorer_name で分岐し、case-evaluations / run-metrics でも metric_name 単位で別 row として保存される。
- payload 系 threshold は未設定で diagnostic row に留まっており、strict gate の pass/fail 判定を置き換える経路は見当たらない。

## 3. unwrap の範囲

- 妥当である。payload helper は text.strip() の後、レスポンス全体が単一 fenced block に fullmatch した場合だけ body を取り出して strip している。
- helper は prose の切り落とし、最初の中括弧抽出、JSON 修復、型 coercion を行っていないため、許容範囲は「前後空白除去 + 単一 fenced block のみ」に収まっている。

## 4. docs と tests の整合

- README と architecture doc は、strict gate と payload diagnostic の違い、対象カテゴリが extraction / constrained_generation に限られること、strict fail を上書きしないことを実装どおりに記述している。
- tests は、bare JSON 正常系、strict fail / payload pass 分離、prose 混在 fail、aggregate_run_metrics への反映を押さえており、今回の変更経路として十分である。

# 成果

## 確認対象

- progress/reviewer/00020-03-review-json-tolerant-metrics.md
- progress/evaluation-analyst/00020-01-verify-live-run-and-scope-json-split.md
- progress/programmer/00020-02-implement-json-tolerant-metrics.md
- src/local_llm_benchmark/benchmark/evaluation.py
- tests/benchmark/test_evaluation.py
- README.md
- docs/architecture/benchmark-foundation.md

## 発見事項

- 未解消の重大 finding はなし。
- strict metric の既存解釈は維持され、payload metric は wrapper cleanliness と payload correctness を読む追加 diagnostic として分離できている。
- unwrap の実装範囲、docs の説明、tests の主要ケースは相互に整合している。

## 残課題

- payload 系で壊れた JSON を fail し続けることを直接固定する専用回帰テストはまだ置かれていない。ただし今回の要求範囲である bare JSON 正常系、strict fail / payload pass 分離、prose 混在 fail は押さえられているため、現時点では blocker ではない。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、reviewer 観点の確認結果は確定してよい。

## 改善提案

- 次に payload 系の堅牢性をさらに固定したい場合は、single fenced block 内の壊れた JSON が payload 側でも fail するケースを 1 本追加すると回帰検知が強くなる。

# 次アクション

- project-master へは、重大 finding なし、strict gate 互換性は維持、残リスクは payload 系の broken JSON 回帰テスト未固定が軽微に残る、という結果を引き継げる。