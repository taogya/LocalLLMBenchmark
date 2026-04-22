---
request_id: "00009"
task_id: "00009-00"
parent_task_id:
owner: "project-master"
title: "roadmap-3-minimum-scope"
status: "done"
depends_on: []
child_task_ids:
  - "00009-01"
  - "00009-02"
  - "00009-03"
  - "00009-04"
  - "00009-05"
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T14:20:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "docs/architecture/benchmark-foundation.md"
  - "prompts"
  - "configs/prompt_sets"
  - "src/local_llm_benchmark/benchmark"
  - "src/local_llm_benchmark/storage"
  - "tests"
---

# 入力要件

- 改善提案 1〜3 が「ロードマップ 3 の最小スコープを決めて着手」に相当するか確認したい。
- 理解が正しければ、その request として進めたい。

# 整理した要件

- 改善提案 1〜3 はロードマップ 3 の具体作業として扱ってよいかを明確化する。
- そのうえで、今回の最小スコープを実装可能な単位へ切り出す。
- prompt、evaluation_reference、case-evaluation / run-metrics 出力の整合を崩さず進める。

# 作業内容

- README、architecture docs、既存 prompt、runner、evaluation snapshot 実装を確認し、現状のロードマップ 3 は sample prompt が classification / extraction / rewrite の 3 件に留まり、case-evaluations.jsonl と run-metrics.json も未実装であることを確認した。
- 改善提案 1〜3 はそのままロードマップ 3 の具体化として扱えると判断した。
- 評価方針、prompt 設計、保存設計、実装、レビューの 5 子タスクへ分けて進める。
- 評価アナリストが、改善提案 1〜3 をまとめてロードマップ 3 の最小完了条件として扱う方針と acceptance criteria を整理した。
- プロンプトアナリストが、summarization / short_qa / constrained_generation の 3 prompt と evaluation_reference の最小形を設計し、既存 rewrite に空の evaluation_reference を足す方針を整理した。
- 設計アーキテクトが、deterministic scorer 実行と run 集計は benchmark 層へ置き、storage は case-evaluations.jsonl と run-metrics.json の書き出し専任に留める方針を整理した。
- programmer が 3 prompt 追加、prompt set の 6 件化、deterministic scorer 実装、case-evaluations / run-metrics 出力、関連 docs と tests 更新を実装した。
- reviewer が 6 カテゴリ解決、evaluation_reference 整合、artifact schema、manual / hybrid 非混入、error case の非集計を確認し、重大 findings なしと判断した。

# 判断

- 最小スコープは「未実装 3 カテゴリの sample prompt を追加し、全 sample prompt の evaluation_reference を machine-readable にそろえ、固定 deterministic scorer に基づく case-evaluations.jsonl と run-metrics.json を出力する」までを第一候補とする。
- similarity / rouge_like / factuality_check のような manual または hybrid 領域は今回の最小スコープに含めない。
- 上記 1〜3 はロードマップ 3 の具体作業として受け取ってよく、今回の request 00009 はその最小スライスを end-to-end で実装する request として妥当だった。

# 成果

- request_id 00009 の親記録を作成した。
- 6 カテゴリ各 1 prompt をそろえ、[configs/prompt_sets/core-small-model-ja-v1.toml](configs/prompt_sets/core-small-model-ja-v1.toml) から 6 prompt を解決できる状態にした。
- `prompts/summarization/meeting-notice-summary-v1.toml`、`prompts/short_qa/support-hours-answer-v1.toml`、`prompts/constrained_generation/followup-action-json-v1.toml` を追加し、既存 `prompts/rewrite/polite-rewrite-v1.toml` に空の evaluation_reference を追加した。
- deterministic scorer 実行 helper と run 集計 helper を benchmark 層へ追加し、classification、extraction、rewrite、summarization、short_qa、constrained_generation の固定 metric を case 単位と run 単位で出力できる状態にした。
- 既定の保存先 `tmp/results/<run_id>/` に `case-evaluations.jsonl` と `run-metrics.json` を追加し、records / raw / case evaluations / run metrics の 4 系統を出力できる状態にした。
- README と architecture docs を更新し、ロードマップ 3 を「最小スライス実装済み」として反映した。
- 関連検証として unit test は reviewer 再実行時点で 18 tests, OK, 3 skip、programmer 検証時点で 20 tests 成功、3 skip、live smoke 3 件成功を確認した。

# 次アクション

- ロードマップ 3 の次段として、CLI 経路で case-evaluations / run-metrics の中身まで固定する golden 検証を追加するかを判断する。
- quality 系の次段として similarity / rouge_like / factuality_check の扱いを manual / hybrid 前提で別 request 化する。
- 次の大きな節目として、ロードマップ 4 の provider 拡張を request 化して進められる状態になった。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md
- docs/architecture/benchmark-foundation.md
- prompts
- configs/prompt_sets
- src/local_llm_benchmark/benchmark
- src/local_llm_benchmark/storage
- tests