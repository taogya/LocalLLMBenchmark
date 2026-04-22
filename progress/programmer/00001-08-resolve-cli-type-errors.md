---
request_id: "00001"
task_id: "00001-08"
parent_task_id: "00001-00"
owner: "programmer"
title: "resolve-cli-type-errors"
status: "done"
depends_on:
  - "00001-07"
created_at: "2026-04-17T20:10:00+09:00"
updated_at: "2026-04-17T20:40:55+09:00"
related_paths:
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/benchmark/models.py"
  - "src/local_llm_benchmark/prompts/repository.py"
  - "src/local_llm_benchmark/providers/ollama/adapter.py"
  - "src/local_llm_benchmark/providers/ollama/client.py"
---

# 入力要件

- cli/main.py に残っている型診断を解消する。
- 既存の振る舞い、docs、tests を壊さない。

# 整理した要件

- root cause を直し、`# type: ignore` のような回避は避ける。
- 必要なら Protocol 整合や dataclass 初期化まわりを見直す。
- 検証結果は progress に記録する。

# 作業内容

- `GenerationSettings`、`OllamaClient`、`OllamaAdapter` に明示的な `__init__` を追加し、CLI から使っている named parameter を型チェッカーが確実に認識できるようにした。
- `InMemoryPromptRepository.resolve_prompt_ids` と `resolve_prompt_set_ids` の引数型を `Sequence[str]` に広げ、`PromptRepository` Protocol と一致させた。
- 今回触ったモジュールの docstring に task_id 00001-08 を追記し、修正の由来を追えるようにした。

# 判断

- named parameter エラーの根本原因は、定義側が dataclass 自動生成 `__init__` に依存しており、現行の型診断環境で CLI 側からの keyword 引数が安定して解決されていなかったことと判断した。
- 呼び出し側を位置引数へ寄せると可読性を落とすうえに対症療法になるため、定義側で明示シグネチャを持たせる方が最小で妥当と判断した。
- `PromptRepository` 不整合は `InMemoryPromptRepository` が `list[str] | tuple[str, ...]` に型を狭めていたことが原因で、Protocol 側に合わせて `Sequence[str]` に寄せるのが自然と判断した。

# 検証

- `get_errors` を `src/local_llm_benchmark/cli/main.py`、`benchmark/models.py`、`prompts/repository.py`、`providers/ollama/client.py`、`providers/ollama/adapter.py` に対して実行し、対象診断が 0 件になったことを確認した。
- `PYTHONPATH=src python -m unittest tests.cli.test_main tests.prompts.test_repository tests.providers.test_ollama_adapter tests.benchmark.test_runner` を実行し、5 tests が成功した。

# 検証制約

- src レイアウトのため、unit test 実行時は `PYTHONPATH=src` を前提にした。
- 実 Ollama API への接続確認は今回の型修正タスク範囲外とし、既存の単体テストによる回帰確認に留めた。

# 成果

- `cli/main.py` に出ていた `OllamaClient`、`GenerationSettings`、`OllamaAdapter` の named parameter 診断を解消した。
- `InMemoryPromptRepository` が `PromptRepository` Protocol と整合する状態に戻した。
- 既存 CLI と関連テストの振る舞いを維持したまま、型診断を 0 件にできた。

# 次アクション

- reviewer が最終確認に入る際は、今回の修正が型シグネチャ明示と Protocol 整合に限定されている点を前提に確認する。

# 関連パス

- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/benchmark/models.py
- src/local_llm_benchmark/prompts/repository.py
- src/local_llm_benchmark/providers/ollama/adapter.py
- src/local_llm_benchmark/providers/ollama/client.py