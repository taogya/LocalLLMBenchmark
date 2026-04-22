---
request_id: "00013"
task_id: "00013-00"
parent_task_id:
owner: "project-master"
title: "ollama-retest-and-openai-compatible-prep"
status: "done"
depends_on: []
child_task_ids:
  - "00013-01"
  - "00013-02"
created_at: "2026-04-18T21:00:00+09:00"
updated_at: "2026-04-18T21:35:00+09:00"
related_paths:
  - "README.md"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "tests/cli/test_live_smoke.py"
  - "progress/programmer/00013-01-rerun-ollama-live-checks.md"
  - "progress/reviewer/00013-02-review-ollama-retest.md"
  - "tmp/runtime-checks/request-00013-20260418-151043"
---

# 入力要件

- Ollama を起動したので再テストしてほしい。
- OpenAI-compatible local server は未準備。
- OpenAI-compatible を試すには benchmark suite と model を追加する必要があるのか確認したい。
- 今回の確認範囲がそこまで含んでいたかを明確にしたい。
- 必要なら provider を準備するので、LM Studio でよいか、推奨モデルがあるか知りたい。

# 整理した要件

- 必須要件は、Ollama 環境での success-path を再テストし、完走可否と評価レポートの状態を確認すること。
- 必須要件は、OpenAI-compatible local server について、今回の確認範囲と追加で必要な準備を切り分けて説明すること。
- 任意要件は、OpenAI-compatible local server の候補実装と、初回確認に向くモデル候補を提案すること。

# 作業内容

- 再テスト専用の子タスクを起票し、programmer に Ollama live smoke と README の `suites -> run -> report` 経路確認を委譲した。
- programmer が Ollama API 応答、必要 3 モデルの存在、live smoke 3 件成功、`request-00013-20260418-151043` の run artifact 生成、report 読み出しまで実施した。
- reviewer に、保存済み artifact と report 表示の整合性、metric fail の原因、`macro_f1=0.25` の説明、OpenAI-compatible の切り分け妥当性を最終確認させた。
- reviewer は重大 finding なしと判断し、今回の recorded success-path は Ollama について完走扱いでよいこと、OpenAI-compatible は別準備が必要な別確認でよいことを確認した。

# 判断

- 今回の主眼は request 00012 で未達だった environment readiness のうち、Ollama success-path を再確認することにあり、その目的は達成できた。
- `manifest.json` の `status = completed`、`record_count = 18`、`records.jsonl` の全件 `error = null`、`raw/` 18 ファイル、`run-metrics.json` 27 rows が整合しているため、今回の recorded run は完走扱いでよい。
- report 上の fail は接続不良や保存不良ではなく、fenced code block 付き JSON、required phrase 不一致、文字数条件未達など、現行 deterministic scorer 条件にモデル出力が合わなかったことに起因する。
- classification の `macro_f1=0.25` は異常ではない。現行 sample は 1 case かつ label_space 4 ラベル固定なので、1 正解時の macro 平均として自然な値である。
- OpenAI-compatible local server の live 確認は今回の必須範囲ではない。既定 suite と live smoke は Ollama 前提であり、OpenAI-compatible を通すには少なくとも server 起動、model alias、必要に応じて provider profile / suite の準備が要る。

# 成果

- request_id 00013 の親記録を完了状態へ更新した。
- Ollama については、API 応答、必要 3 モデル、live smoke、README の `suites -> run -> report` 経路がすべて通ることを確認した。
- 実 run `tmp/runtime-checks/request-00013-20260418-151043` では `records: 18`、`errors: 0`、`metric_rows: 27` で、保存 artifact と report 読み出しが整合した。
- metric fail は runtime failure ではなく評価条件不一致であり、現行 deterministic scorer が働いていることを artifact ベースで確認した。
- OpenAI-compatible は今回の確認範囲外として切り分けてよく、次に確認するなら別 request で server と model alias を含めて扱うのが妥当だと整理した。
- ユーザー報告可能な状態まで統合できた。

# 次アクション

- ユーザーへ、Ollama の success-path は完走したこと、report fail は scorer 条件起因であること、OpenAI-compatible は別準備が必要であることを報告する。
- OpenAI-compatible を次に進める場合は、`provider_id = "openai_compatible"` の model を含む最小 suite か opt-in smoke を別 request で用意する。

# 関連パス

- README.md
- configs/benchmark_suites/local-three-tier-baseline-v1.toml
- tests/cli/test_live_smoke.py