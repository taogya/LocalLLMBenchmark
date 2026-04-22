---
request_id: "00016"
task_id: "00016-02"
parent_task_id: "00016-00"
owner: "programmer"
title: "implement-lmstudio-docs-and-openai-minimum-suite"
status: "done"
depends_on:
  - "00016-01"
created_at: "2026-04-18T23:40:00+09:00"
updated_at: "2026-04-18T18:42:22+09:00"
related_paths:
  - "progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md"
  - "progress/solution-architect/00016-01-design-lmstudio-readiness-and-minimal-suite.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/lmstudio/README.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "configs/benchmark_suites/openai-compatible-minimal-v1.toml"
  - "configs/prompt_sets/minimal-readiness-ja-v1.toml"
  - "src/local_llm_benchmark/providers/openai_compatible/client.py"
  - "tests/cli/test_live_smoke.py"
  - "tests/cli/test_main.py"
  - "tests/config/test_loader.py"
  - "tmp/runtime-checks/request-00016-20260418-184120"
---

# 入力要件

- 設計結果に基づき、LM Studio セットアップ文書、OpenAI-compatible の最小 suite、必要なら live smoke や補助コードを実装する。
- 可能なら LM Studio か別の OpenAI-compatible local server で 1 本 run を通し、証跡を残す。

# 作業内容

- `docs/lmstudio/README.md` を追加し、`lms` と LM Studio の関係、初回起動、`lms get` -> `lms server start` -> `lms load --identifier llmb-minimal-chat` の順、`/v1/models` 確認、benchmark 実行コマンド、Bonsai 8B fallback を短く追記した。
- `README.md` に LM Studio docs への導線と、`openai-compatible-minimal-v1` の最小実行例を追記した。既存の Ollama 既定導線は変更していない。
- `docs/architecture/benchmark-foundation.md` に、OpenAI-compatible readiness では server start と explicit model load を分けることと、`openai-compatible-minimal-v1` が readiness 専用 suite であることを追記した。
- `configs/model_registry/openai-compatible-readiness.toml`、`configs/prompt_sets/minimal-readiness-ja-v1.toml`、`configs/benchmark_suites/openai-compatible-minimal-v1.toml` を追加し、1 model x 3 prompts の OpenAI-compatible minimal suite を実装した。
- `tests/config/test_loader.py` と `tests/cli/test_main.py` に新しい suite / model / prompt set の解決確認を追加した。
- `tests/cli/test_live_smoke.py` に OpenAI-compatible 用の opt-in live smoke を追加し、`LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE`、`/v1/models`、alias 確認、suite -> run -> report を最小責務として実装した。既存 Ollama smoke は維持した。
- `src/local_llm_benchmark/providers/openai_compatible/client.py` は設計どおり変更していない。
- live run は `lms` 不在のため LM Studio 本経路は試せず、fallback として Ollama の OpenAI-compatible endpoint を一時 config で使って `openai-compatible-minimal-v1` を完走確認した。

# 判断

- provider core の必須変更は発生しなかったため、docs / config / tests の追加に留めた。
- OpenAI-compatible live smoke は repo の恒久設定を変えず、既定の `configs/provider_profiles/openai-compatible-local.toml` を基準にしたまま opt-in で追加した。
- smoke の alias 判定は `GET /v1/models` に exact alias `llmb-minimal-chat` が見えることを維持した。fallback に使った Ollama は `llmb-minimal-chat:latest` を返したため、自動 smoke の前提とは分けて扱う。
- live run は repo の LM Studio 既定 profile を 11434/v1 に変えず、`tmp/runtime-checks/request-00016-20260418-184120/configs` に一時 config を作って fallback を試した。恒久設定を汚さずに実 run だけを確認するためである。
- strict / tolerant split と sentence_count explainability は今回の blocker ではないため実装していない。

# 成果

- docs、config、tests の必須範囲は完了した。
- `python -m unittest tests.config.test_loader tests.cli.test_main tests.cli.test_live_smoke` は 30 tests, OK, skipped=6 だった。
- `lms` はこの環境で未導入、`http://localhost:1234/v1/models` は未起動だったため、LM Studio 本経路の live 検証はできなかった。
- fallback として `http://localhost:11434/v1` の Ollama OpenAI-compatible endpoint を使い、`ollama cp qwen2.5:7b llmb-minimal-chat` で alias を作成したうえで live run を実施した。
- live run の証跡は次のとおり。
  - server: Ollama OpenAI-compatible endpoint (`http://localhost:11434/v1`)
  - backing model: `qwen2.5:7b` を `llmb-minimal-chat` alias へ copy したもの
  - run_id: `request-00016-live-20260418-184120`
  - run_dir: `tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120`
  - config root: `tmp/runtime-checks/request-00016-20260418-184120/configs`
  - suite: `openai-compatible-minimal-v1`
  - result summary: 3 records, 0 errors, `accuracy=1.0`, `macro_f1=0.25`, `exact_match_rate=1.0`, `json_valid_rate=1.0(pass)`, `short_qa exact_match_rate=1.0`

# 次アクション

- reviewer が LM Studio docs の粒度、readiness 専用 suite の位置付け、OpenAI-compatible smoke の skip 条件、fallback live run の扱いを最終確認する。

# 検証

- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.config.test_loader tests.cli.test_main tests.cli.test_live_smoke`
  - 30 tests, OK, skipped=6
- `command -v lms`
  - exit code 1。`lms` は未導入
- `curl -fsS http://localhost:1234/v1/models`
  - exit code 7。LM Studio 既定 endpoint は未起動
- `curl -fsS http://localhost:11434/v1/models`
  - Ollama OpenAI-compatible endpoint は応答。`llmb-minimal-chat:latest` を含む model list を確認
- `ollama show llmb-minimal-chat >/dev/null 2>&1 || ollama cp qwen2.5:7b llmb-minimal-chat`
  - fallback alias を作成
- `source .venv/bin/activate && ts=$(date +%Y%m%d-%H%M%S) && workdir="tmp/runtime-checks/request-00016-$ts" && run_id="request-00016-live-$ts" && mkdir -p "$workdir" && cp -R configs "$workdir/configs" && cp -R prompts "$workdir/prompts" && perl -0pi -e 's#http://localhost:1234/v1#http://localhost:11434/v1#' "$workdir/configs/provider_profiles/openai-compatible-local.toml" && PYTHONPATH=src local-llm-benchmark suites openai-compatible-minimal-v1 --config-root "$workdir/configs" && PYTHONPATH=src local-llm-benchmark run --config-root "$workdir/configs" --suite openai-compatible-minimal-v1 --run-id "$run_id" --output-dir "$workdir/results" && PYTHONPATH=src local-llm-benchmark report --run-dir "$workdir/results/$run_id"`
  - fallback live run 成功。`request-00016-live-20260418-184120` を保存

# リスク

- LM Studio 専用の live 検証は、この環境で `lms` がないため未確認である。
- OpenAI-compatible live smoke は exact alias `llmb-minimal-chat` を `/v1/models` に要求する。Ollama fallback は `llmb-minimal-chat:latest` を返すため、この smoke の前提は満たさない。
- alias-backed readiness slot は実行しやすい反面、正式比較で backing model の取り違えが起きやすい。比較用途では actual model ごとの model_key を別に切る必要がある。

# 改善提案

- LM Studio 実機で `lms` が使える環境では、`LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke` を 1 回通し、`/v1/models` の exact alias 前提も含めて確認するとよい。
- OpenAI-compatible fallback を定常運用したくなったら、profile 複製ではなく一時 config root を作る helper task を別 request で切り出すと live check の再現性が上がる。
