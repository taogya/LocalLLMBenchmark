---
request_id: "00001"
task_id: "00001-06"
parent_task_id: "00001-00"
owner: "programmer"
title: "stabilize-and-verify"
status: "done"
depends_on:
  - "00001-03"
created_at: "2026-04-17T19:00:00+09:00"
updated_at: "2026-04-17T19:40:00+09:00"
related_paths:
  - "src/local_llm_benchmark"
  - "tests"
  - "pyproject.toml"
---

# 入力要件

- 既存の初期スキャフォールドを壊さずに、src/tests に残っているスタイル診断を解消する。
- CLI と unit test を実行し、今回追加した基盤の最小動作を確認する。

# 整理した要件

- 機能追加ではなく、00001-03 の仕上げとして整合修正と検証を行う。
- 既存の public API や docs の説明を必要以上に変えない。
- テストや検証で判明した注意点は progress へ残す。

# 作業内容

- src/local_llm_benchmark/prompts/repository.py の dict 内包表記を折り返し、行長超過を解消した。
- src/local_llm_benchmark/providers/ollama/adapter.py の import、message 構築、例外送出を折り返し、行長超過を解消した。
- src/local_llm_benchmark/providers/ollama/client.py の末尾空行を除去した。apply_patch だけでは末尾の二重改行が消えなかったため、terminal で改行数を確認し、末尾改行の正規化を実施した。
- src/local_llm_benchmark/cli/main.py の parser 構築、handler シグネチャ、list 内包表記、GenerationSettings、print 呼び出しを折り返し、行長超過を解消した。
- tests/benchmark/test_runner.py、tests/cli/test_main.py、tests/prompts/test_repository.py、tests/providers/test_ollama_adapter.py の import、長い引数列、assertion を折り返し、行長超過を解消した。

# 判断

- 要求はスタイル診断の解消であり、既存ロジックや public API を変えないことを優先した。
- test_runner の長いテスト名だけは診断解消のため短縮したが、検証意図は維持した。
- unit test の初回実行は `local_llm_benchmark` を import できず失敗したため、editable install 未実施の src レイアウト環境として扱い、`PYTHONPATH=src` で再実行して検証した。
- ローカル Ollama の起動有無はこのタスクでは前提にせず、ネットワーク依存の実 API 実行までは広げない方が安全と判断した。

# 検証

- `get_errors` を src と tests に対して実行し、今回の対象診断が 0 件になったことを確認した。
- `python -m unittest tests.benchmark.test_runner tests.cli.test_main tests.prompts.test_repository tests.providers.test_ollama_adapter` は import path 未設定のため失敗し、原因が src レイアウト未導入であることを確認した。
- `PYTHONPATH=src python -m unittest tests.benchmark.test_runner tests.cli.test_main tests.prompts.test_repository tests.providers.test_ollama_adapter` を実行し、5 tests が成功した。
- `PYTHONPATH=src python -m local_llm_benchmark --help` を実行し、CLI help が表示されることを確認した。

# 検証制約

- editable install は今回のタスク範囲に含めず、import path は `PYTHONPATH=src` で補った。
- 実 Ollama API への接続確認は、ローカル起動状態に依存するため今回は未実施とした。

# 成果

- src/tests のスタイル診断を最小変更で解消し、get_errors で対象エラー 0 件を確認した。
- 修正範囲の unit test と CLI help の最小検証結果を記録できる状態にした。
- 初期スキャフォールドの責務分割と task_id 記述を維持したまま整合性を上げた。

# 次アクション

- reviewer が最終確認に入る際は、今回の import path 前提と実 API 未実行の制約を踏まえて確認する。
- 次段階で実 CLI 実行を行う場合は、editable install または共通の test 実行ラッパーを用意すると検証手順がぶれにくい。

# 関連パス

- src/local_llm_benchmark
- tests
- pyproject.toml