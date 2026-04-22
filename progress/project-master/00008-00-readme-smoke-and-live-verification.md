---
request_id: "00008"
task_id: "00008-00"
parent_task_id:
owner: "project-master"
title: "readme-smoke-and-live-verification"
status: "done"
depends_on: []
child_task_ids:
  - "00008-01"
  - "00008-02"
created_at: "2026-04-18T12:50:00+09:00"
updated_at: "2026-04-18T13:25:00+09:00"
related_paths:
  - "README.md"
  - "docs/ollama/api-check.md"
  - "tests/cli"
  - "tmp"
---

# 入力要件

- README の最小実行セクションに追加したコメントが問題ないか確認したい。
- 前回の改善提案である success-path smoke を実装したい。
- ユーザー環境では sample suite の 3 モデルが既に pull 済みである。
- 完了後は次のロードマップへ進みたい。

# 整理した要件

- README の現状を確認し、必要なら最小限の文言調整に留める。
- `suites` -> `run` の流れをそのまま確認できる opt-in の live smoke を追加する。
- 通常の unit test を壊さず、live 環境があるときだけ実行できる形にする。
- 実環境で可能なら smoke を実行し、成功系の確認まで進める。

# 作業内容

- README と既存 docs を確認し、コメント追加は概ね妥当であること、ただし suite detail のコメントは「設定を読む」より「詳細と準備対象を確認」の方が実態に近いことを把握した。
- docs/ollama/api-check.md には run の確認導線はあるが、`suites` を含む success-path smoke の固定手順はまだないことを確認した。
- 実装とレビューの 2 子タスクへ分けて進める。
- programmer が `tests/cli/test_live_smoke.py` を追加し、`LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE` が truthy のときだけ動く opt-in live smoke を実装した。
- programmer が README と docs/ollama/api-check.md に live smoke の実行方法を短く追記し、README の suite detail コメントを実態に合わせて最小修正した。
- reviewer が docs のモデル名表記を sample suite と一致する `gemma3:latest` にそろえ、通常 skip と opt-in 実行成功の両方を確認した。

# 判断

- ここでは新機能追加ではなく、既存 CLI の実利用導線を固定化する smoke の追加が主目的であるため、設計専任タスクは省略し、programmer と reviewer の 2 段で進める。
- live smoke は通常 test suite から分離し、明示 opt-in の環境変数でのみ実行する形が妥当である。
- README のコメント追加は問題なく、流れも user-friendly である。修正は suite detail の意味を実態に合わせる最小変更だけで十分である。
- live smoke は約 52-105 秒の実環境依存処理になるため、CI 常設ではなく opt-in 運用を維持するのが現実的である。

# 成果

- request_id 00008 の親記録を作成した。
- README の最小実行セクションは概ね問題なく、`local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs` のコメントを「詳細と準備対象を確認」へ最小修正した。
- `tests/cli/test_live_smoke.py` に、README 記載の `suites` -> `run` をそのまま確認する opt-in live smoke を追加した。
- live smoke は Ollama version / tags を事前確認し、未起動や必要モデル不足なら理由付きで skip し、run 成功時は `manifest.json`、`records.jsonl`、`raw/` の生成まで確認する。
- README と `docs/ollama/api-check.md` に `LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke` の導線を追加した。
- reviewer により docs 上の `gemma3` 表記は `gemma3:latest` へ整合された。
- 検証として、通常実行では live smoke 3 件が skip、opt-in 実行では live smoke 3 件が成功した。関連ファイルの diagnostics は 0 件である。

# 次アクション

- 次のロードマップとして、評価データ整備に着手する。具体的には sample prompt の拡張、evaluation_reference の整備、case-evaluations / run-metrics 出力の優先順位を整理して request 化する。
- 将来 CI へ寄せる場合は、provider 非依存の contract smoke と実環境 live smoke を分離する方針を検討する。

# 関連パス

- README.md
- docs/ollama/api-check.md
- tests/cli
- tmp