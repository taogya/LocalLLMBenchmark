---
request_id: "00012"
task_id: "00012-02"
parent_task_id: "00012-00"
owner: "programmer"
title: "implement-secret-env-and-validate-runtime"
status: "done"
depends_on:
  - "00012-01"
created_at: "2026-04-18T19:20:00+09:00"
updated_at: "2026-04-18T14:31:34+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/providers/factory.py"
  - "tests/config/test_loader.py"
  - "tests/providers/test_factory.py"
  - "tests/providers/test_openai_compatible_client.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_live_smoke.py"
---

# 入力要件

- API キー平文を避けるよう実装と文書を更新したい。
- 実際に benchmark が動くか可能な範囲で確認したい。

# 整理した要件

- secret は config の値ではなく環境変数名参照に切り替える。
- runtime 検証は unit test に加え、環境が許せば live smoke と sample run / report まで進める。
- provider 非依存境界を守るため、`config` 層ではなく `providers/factory.py` だけで `api_key_env` を解決する。
- OpenAI-compatible local server は keyless を既定にし、認証が必要なときだけ明示 env 参照を受け付ける。

# 作業内容

- `configs/provider_profiles/openai-compatible-local.toml` から平文 `connection.api_key` を削除し、keyless 既定を維持したまま `api_key_env = "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY"` のコメント例へ置き換えた。
- `src/local_llm_benchmark/providers/factory.py` に OpenAI-compatible 専用の helper を追加し、`connection.api_key` を reject、`connection.api_key_env` のみを解決するようにした。`api_key_env` 未指定時は `None` を返し、参照先環境変数が未設定または空文字なら `ValueError` で fail fast する。暗黙 fallback は追加していない。
- `tests/providers/test_factory.py` を更新し、keyless 正常系、`api_key_env` 正常系、`api_key_env` 未設定 error、旧 `api_key` reject を追加した。
- `tests/config/test_loader.py` を更新し、sample profile が `base_url` と `timeout_seconds` を維持しつつ、平文 `api_key` を含まない形で load できることを固定した。
- `README.md` に OpenAI-compatible local server の secret 運用と、`code readiness` / `environment readiness` の短い説明を追加した。
- `docs/architecture/benchmark-foundation.md` に、config loader は secret を読まず provider factory が明示 env 参照だけを解決することと、OpenAI-compatible の auth 契約、readiness の切り分けを追記した。

# 判断

- secret 解決は provider 固有契約なので、`ProviderProfile.connection` を generic mapping のまま保ち、OpenAI-compatible 分岐の factory helper に閉じ込める方針を維持した。
- keyless server を壊さないため、`api_key_env` は任意のままとし、未指定時は Authorization header なしで client へ渡す契約を採用した。
- `api_key_env` を明示したのに値が取れないケースは user の設定ミスとみなし、無認証へ降格せず fail fast する方が安全である。
- 現在の環境では Ollama と OpenAI-compatible local server の両方が未起動で、environment readiness の success-path までは進めないことを blocker として記録する。

# 成果

## 変更したファイル

- `configs/provider_profiles/openai-compatible-local.toml`
- `src/local_llm_benchmark/providers/factory.py`
- `tests/providers/test_factory.py`
- `tests/config/test_loader.py`
- `README.md`
- `docs/architecture/benchmark-foundation.md`

## 実装内容

- OpenAI-compatible sample profile は keyless 既定へ切り替わり、平文 API キーを repo 内へ置かない形になった。
- factory は `connection.api_key_env` の明示参照だけを解決し、`connection.api_key` は migration error として reject するようになった。
- README と architecture doc に、secret 運用と readiness の切り分けを初心者向けに短く追加した。

## 検証内容

- `get_errors` で `src/local_llm_benchmark/providers/factory.py`、`tests/providers/test_factory.py`、`tests/config/test_loader.py`、`README.md`、`docs/architecture/benchmark-foundation.md` の診断 0 件を確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.providers.test_openai_compatible_client tests.providers.test_factory tests.config.test_loader tests.cli.test_main`
  - 23 tests, OK
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
  - Ollama API へ接続できず skip。現在環境では success-path live smoke は未確認。
- `source .venv/bin/activate && local-llm-benchmark suites --config-root configs`
  - suite 一覧表示に成功。code readiness の最初の段階は確認できた。
- `source .venv/bin/activate && local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs`
  - suite detail と required model identifier 表示に成功。config 解決は維持できている。
- `source .venv/bin/activate && local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id request-00012-runtime-20260418-1 --output-dir tmp/runtime-checks`
  - 18 records の計画生成と artifact 保存までは成功。Ollama 未起動のため 18 件すべて `Connection refused` で environment readiness は blocker。
- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/runtime-checks/request-00012-runtime-20260418-1`
  - failure artifact の読込に成功。`records=18`、`metric_rows=0`、scope mismatch note を確認した。
- `curl -fsS http://localhost:1234/v1/models`
  - `localhost:1234` へ接続できず。OpenAI-compatible local server の live 確認は現環境では blocker。

## readiness 状態

- code readiness: `suites` と suite detail は通過。README / docs / factory / sample profile の整合は unit test と CLI 表示で確認できた。
- environment readiness: Ollama 未起動のため default suite の `run` 成功は未確認。OpenAI-compatible local server も `localhost:1234` に疎通できず live auth 契約までは未確認。

# 次アクション

- reviewer が provider 非依存境界、`api_key` reject、`api_key_env` fail fast、README / architecture doc の記述整合を確認する。
- success-path を確認する場合は、Ollama を起動して live smoke を再実行し、OpenAI-compatible local server を `localhost:1234/v1` で起動したうえで auth 有無の疎通を別 request で確認する。

# リスク

- 既存の custom profile で `connection.api_key` を使っていた場合は非互換になる。
- OpenAI-compatible local server の live 確認は未実施で、現時点では unit test と sample 接続先の blocker 確認までに留まる。

# 改善提案

- OpenAI-compatible provider 用の opt-in live smoke を別 request で追加すると、`api_key_env` 契約の回帰を CLI 経路でも検知しやすい。
- provider が増えて env 参照契約が複数に広がった段階で、generic な secret reference 形式を別 request で検討するとよい。

# 関連パス

- configs/provider_profiles/openai-compatible-local.toml
- src/local_llm_benchmark/providers/factory.py
- tests/providers/test_factory.py