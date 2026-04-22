---
request_id: "00008"
task_id: "00008-02"
parent_task_id: "00008-00"
owner: "reviewer"
title: "review-live-smoke"
status: "done"
depends_on:
  - "00008-01"
created_at: "2026-04-18T12:50:00+09:00"
updated_at: "2026-04-18T12:50:00+09:00"
related_paths:
  - "README.md"
  - "docs/ollama/api-check.md"
  - "tests/cli/test_live_smoke.py"
  - "tmp"
---

# 入力要件

- live smoke の妥当性と、可能なら実環境での確認まで行いたい。

# 整理した要件

- README の最小実行セクション、docs/ollama/api-check.md、tests/cli/test_live_smoke.py を相互に照合する。
- opt-in live smoke が通常 unittest を壊さないことと、可能なら実環境で成功することを確認する。
- README と docs の導線、skip 条件、生成 artifact の説明に重大な抜けがないか確認する。

# 作業内容

- README.md の最小実行セクション差分を確認し、suite detail のコメント修正が実態に沿った最小変更であることを確認した。
- docs/ollama/api-check.md と sample config を照合し、live smoke 導線と skip 条件が README と概ね一致していることを確認した。
- tests/cli/test_live_smoke.py を確認し、通常時は env var 未設定で class 全体が skip され、opt-in 時のみ suites 一覧、suite 詳細、run と artifact 生成を確認する構成であることを確認した。
- `PYTHONPATH=src python -m unittest tests.cli.test_live_smoke -v` を実行し、3 tests が既定で skip されることを確認した。
- `PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v` を実行し、3 tests, OK を確認した。
- `ollama list` を実行し、sample suite が要求する `gemma3:latest`、`qwen2.5:7b`、`llama3.1:8b` が存在することを確認した。
- docs/ollama/api-check.md で `gemma3` と書かれていた例を sample suite の実際のタグ `gemma3:latest` にそろえる最小修正を行った。

# 判断

- README のコメント追加は flow を変えず、`suites` サブコマンドの実出力に合わせた説明への言い換えに留まっており、過剰な変更ではない。
- live smoke は `LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE` が truthy のときだけ有効なため、通常の unittest 実行を壊さない。
- Ollama 未起動時は version / tags API の事前確認で skip し、必要モデル不足時も skip 理由を返すため、失敗原因の切り分けは十分に分かりやすい。
- smoke は README の `suites` -> `run` 導線をそのまま押さえつつ、`manifest.json`、`records.jsonl`、`raw/` の生成確認まで行っており、artifact とコマンド導線の確認範囲は妥当である。
- docs と README の live smoke コマンドは一致しており、今回の修正でモデル名表記も sample config と一致した。

# 成果

- 重大な findings は確認されなかった。
- 軽微な整合差として、docs/ollama/api-check.md のモデル名表記が sample suite の実タグと完全一致していなかったため修正した。
- request 00008 は live smoke を次のロードマップへ進める前提として問題ないと判断した。

# 確認対象

- README.md
- docs/ollama/api-check.md
- tests/cli/test_live_smoke.py
- sample config とローカル Ollama 実環境

# 発見事項

- minor: docs/ollama/api-check.md の chat API 例と failure tip が `gemma3` 表記のままで、sample suite と model registry が使う `gemma3:latest` と完全一致していなかった。レビュー時に修正済み。

# 検証

- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_live_smoke -v`
  - 3 tests, OK, skipped=3
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
  - 3 tests, OK
- `source .venv/bin/activate && ollama list`
  - `gemma3:latest`、`qwen2.5:7b`、`llama3.1:8b` を確認

# 残課題

- live smoke は実環境依存で約 52 秒かかるため、CI 常設ではなく現状どおり opt-in 運用が前提となる。

# ユーザー報告可否

- 報告可。重大な抜けは見当たらず、軽微な文書整合差は修正済み。

# 改善提案

- 将来 CI へ寄せる場合は、provider を抽象化した contract smoke と live smoke を分離し、live 側だけを手動または専用環境で走らせる運用にすると管理しやすい。

# 次アクション

- project-master へ、重大な findings なしと軽微な docs 修正済み、live smoke 実測成功を統合する。

# 関連パス

- README.md
- docs/ollama/api-check.md
- tests/cli/test_live_smoke.py
- tmp