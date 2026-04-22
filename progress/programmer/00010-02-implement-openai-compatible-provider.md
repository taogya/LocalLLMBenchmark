---
request_id: "00010"
task_id: "00010-02"
parent_task_id: "00010-00"
owner: "programmer"
title: "implement-openai-compatible-provider"
status: "done"
depends_on:
  - "00010-01"
created_at: "2026-04-18T14:35:00+09:00"
updated_at: "2026-04-18T18:05:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/providers"
  - "src/local_llm_benchmark/providers/openai_compatible"
  - "src/local_llm_benchmark/config"
  - "configs/provider_profiles"
  - "tests/providers"
  - "tests/config"
  - "tests/cli"
---

# 入力要件

- OpenAI-compatible local provider を実装したい。

# 整理した要件

- provider_id は openai_compatible とし、provider 差分は providers/openai_compatible 配下へ閉じ込める。
- v1 は non-streaming の chat completions API のみを対象にする。
- provider profile は base_url 必須、api_key 任意、timeout_seconds 任意とし、model は model registry の provider_model_name を使う。
- factory dispatch、sample profile、tests、README / architecture docs、progress を最小差分で更新する。

# 作業内容

- src/local_llm_benchmark/providers/openai_compatible/ に adapter.py、client.py、__init__.py を追加し、chat completions の non-streaming 呼び出しと共通 InferenceResponse への正規化を実装した。
- src/local_llm_benchmark/providers/factory.py に openai_compatible の dispatch と builder helper を追加し、connection.base_url / api_key / timeout_seconds の最小検証を実装した。
- configs/provider_profiles/openai-compatible-local.toml を sample profile として追加し、既定 suite を切り替えずに OpenAI-compatible local server の接続先例を同梱した。
- README.md と docs/architecture/benchmark-foundation.md を最小更新し、openai_compatible provider の位置づけと sample profile 利用方針を追記した。
- tests/providers/test_openai_compatible_adapter.py、tests/providers/test_openai_compatible_client.py、tests/providers/test_factory.py を追加し、tests/config/test_loader.py を最小更新した。

# 判断

- seed は OpenAI-compatible v1 では payload へ送らない方針を採用した。ローカル server 実装ごとの差が大きく、最小スライスでは相互運用性を優先したためである。
- OpenAI-compatible server 固有の help や起動コマンドは provider 非依存層へ持ち込まず、README と architecture docs では provider profile と model registry の責務だけを短く説明する粒度に留めた。
- sample profile は追加したが、既定 suite や sample model registry は Ollama のまま維持し、既存導線を壊さない構成にした。

# 成果

- OpenAI-compatible local server を provider profile と model registry の組み合わせで接続できる最小 provider 実装が追加された。
- factory は ollama と openai_compatible を同じ dispatch 境界で組み立てられるようになった。
- unit test で adapter / client / factory / config sample の最小回帰を押さえられる状態になった。

# 検証

- get_errors で変更ファイルの診断を確認する。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.providers.test_ollama_adapter tests.providers.test_openai_compatible_adapter tests.providers.test_openai_compatible_client tests.providers.test_factory tests.config.test_loader` を実行して、既存 Ollama adapter と新規 OpenAI-compatible provider の unit test を確認する。

# 次アクション

- reviewer が provider 非依存境界、docs、sample profile、unit test の整合を確認する。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/providers
- src/local_llm_benchmark/config
- configs/provider_profiles
- tests/providers
- tests/cli