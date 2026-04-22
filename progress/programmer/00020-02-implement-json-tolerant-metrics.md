---
request_id: "00020"
task_id: "00020-02"
parent_task_id: "00020-00"
owner: "programmer"
title: "implement-json-tolerant-metrics"
status: "done"
depends_on:
  - "00020-01"
created_at: "2026-04-19T14:10:00+09:00"
updated_at: "2026-04-19T13:29:32+09:00"
related_paths:
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/benchmark/test_evaluation.py"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/evaluation-analyst/00020-01-verify-live-run-and-scope-json-split.md"
---

# 要件整理

- strict JSON metric を維持したまま、wrapper cleanliness と payload correctness を分離して読める tolerant JSON metric を最小追加する。
- 既存 CLI / storage / compare surface を壊さない形で実装する。
- unit test と必要最小限の README / architecture doc 更新まで含める。

# 作業内容

- evaluation-analyst の提案どおり、extraction に `json_payload_valid_rate` と `payload_exact_match_rate`、constrained_generation に `payload_format_valid_rate` と `payload_constraint_pass_rate` を追加した。
- `src/local_llm_benchmark/benchmark/evaluation.py` に、前後空白除去とレスポンス全体が単一 fenced block のときだけ wrapper を外す最小 helper を追加し、payload 専用 scorer を strict scorer とは別経路で実装した。
- `tests/benchmark/test_evaluation.py` に、bare JSON 正常系、single fenced JSON の strict fail / payload pass 分離、前後 prose 付き fail、aggregate_run_metrics への反映を追加した。
- `README.md` と `docs/architecture/benchmark-foundation.md` に、strict gate と payload diagnostic の違い、前処理の上限、strict fail を上書きしないことを短く追記した。

# 判断

- strict metric 名、strict scorer の意味、既存 threshold は変更していない。新規 payload metric の threshold は付けず、run gate ではなく diagnostic row として追加した。
- tolerant 前処理は前後空白除去と単一 fenced block unwrap のみに限定し、prose 切り落とし、JSON 修復、最初の中括弧抽出、型 coercion は実装していない。
- 対象カテゴリは extraction と constrained_generation のみに限定し、classification、rewrite、summarization、short_qa の既存挙動は変えていない。

# 成果

## 変更したファイル

- `src/local_llm_benchmark/benchmark/evaluation.py`
- `tests/benchmark/test_evaluation.py`
- `README.md`
- `docs/architecture/benchmark-foundation.md`

## 実装内容

- JSON task の strict row と payload row を別 metric 名で並立させ、single fenced JSON を strict fail / payload pass として区別できるようにした。
- payload 系は raw response 全体が単一 fenced block のときだけ unwrap し、それ以外は strip 後の全文をそのまま採点するため、前後 prose 付き response は引き続き fail になる。
- compare / report / storage 側は metric_name を opaque に扱う前提のため、既存 surface を変えずに新規 row が流れる形に留めた。

## 検証

- `get_errors` で `src/local_llm_benchmark/benchmark/evaluation.py` と `tests/benchmark/test_evaluation.py` の diagnostics 0 件を確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.benchmark.test_evaluation`
  - 5 tests, OK
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.benchmark.test_runner tests.benchmark.test_evaluation`
  - 7 tests, OK

## リスク

- payload 系 metric は `json_valid_rate` と違って extraction では JSON object 必須としているため、parse-only の strict row と意味が完全一致するわけではない。
- unwrap は単一 fenced block に限定しているため、複数 block や prose 混在 response の rescue は行わない。

## 改善提案

- compare や report で payload 系 metric が増えた状態の読みやすさを確認し、必要なら strict / payload を並べる表示補助を別 request で検討するとよい。
- constrained_generation の実 artifact を使った live 比較 fixture が増えると、strict / payload split の回帰をさらに検知しやすい。

# 次アクション

- reviewer が strict gate 互換性と docs 整合を確認できるよう、変更内容と検証結果を残す。