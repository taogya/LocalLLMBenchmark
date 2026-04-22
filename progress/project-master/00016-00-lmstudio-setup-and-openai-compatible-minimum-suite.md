---
request_id: "00016"
task_id: "00016-00"
parent_task_id: null
owner: "project-master"
title: "lmstudio-setup-and-openai-compatible-minimum-suite"
status: "done"
depends_on: []
child_task_ids:
  - "00016-01"
  - "00016-02"
  - "00016-03"
created_at: "2026-04-18T23:40:00+09:00"
updated_at: "2026-04-19T00:55:00+09:00"
related_paths:
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
  - "progress/solution-architect/00016-01-design-lmstudio-readiness-and-minimal-suite.md"
  - "progress/programmer/00016-02-implement-lmstudio-docs-and-openai-minimum-suite.md"
  - "progress/reviewer/00016-03-review-lmstudio-docs-and-openai-minimum-suite.md"
  - "tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/manifest.json"
  - "tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/run-metrics.json"
---

# 要件整理

- LM Studio CLI の導入手順を公式一次情報で確認し、CLI で動かすためのセットアップ方法をドキュメントへ残す。
- LM Studio ではモデルロードが明示的かを確認し、その前提で現状の OpenAI-compatible スクリプトで問題ないかを検証する。
- OpenAI-compatible の最小 suite を作成し、可能なら 1 本 live に通す。
- 前回提案した strict / tolerant split と sentence_count explainability は、今回の目的に対して必須なら対応し、不要なら defer 理由を明示する。

# 作業内容

- LM Studio CLI 公式 docs と既存の OpenAI-compatible 実装、README、live smoke を確認し、今回の変更境界を整理する。
- 設計、実装、最終確認を各 agent へ委譲する。
- solution-architect は、LM Studio readiness を install -> first run -> `lms get` -> `lms server start` -> `lms load --identifier llmb-minimal-chat` -> `/v1/models` -> benchmark 実行、の 1 本の導線として設計した。
- programmer は、LM Studio 向け docs 追加、OpenAI-compatible minimal suite 用 config 追加、opt-in live smoke 追加、loader / CLI tests 更新、fallback OpenAI-compatible live run まで実施した。
- reviewer は、LM Studio readiness 導線と fallback live run の解釈境界を確認し、README と LM Studio docs へ軽微な文言補強を入れて整合性を確定した。

# 判断

- LM Studio は `lms server start` だけでなく `lms load` の明示運用が関わる可能性が高く、environment readiness 文書の補強が必要。
- 既存の OpenAI-compatible client は `/chat/completions` 前提でシンプルなため、コード本体より config / docs / smoke の整備が主論点になる見込み。
- strict / tolerant split と sentence_count の見直しは、本 request の主目的に対する必須性を個別判定する。
- `openai-compatible-minimal-v1` は readiness 専用の 1 model x 3 prompts suite とし、正式比較用 suite と分けて扱うのが妥当である。
- `llmb-minimal-chat` の alias-backed 運用は、Bonsai 8B を含む backing model の差し替えを docs 側へ閉じ込められるため、今回の最小導線に適している。
- strict / tolerant split と sentence_count explainability は今回の blocker ではなく、request 00014 の整理どおり defer でよい。
- fallback live run は OpenAI-compatible 経路の疎通確認としては有効だが、LM Studio 実機 readiness の代替証跡にはしない。

# 成果

- request 00016 を起票した。
- [docs/lmstudio/README.md](docs/lmstudio/README.md) を追加し、LM Studio の install / first run / `lms get` / `lms server start` / `lms load` / `/v1/models` / benchmark 実行を日本語で短く整理した。
- [configs/model_registry/openai-compatible-readiness.toml](configs/model_registry/openai-compatible-readiness.toml)、[configs/prompt_sets/minimal-readiness-ja-v1.toml](configs/prompt_sets/minimal-readiness-ja-v1.toml)、[configs/benchmark_suites/openai-compatible-minimal-v1.toml](configs/benchmark_suites/openai-compatible-minimal-v1.toml) を追加し、OpenAI-compatible minimal suite を実装した。
- [tests/cli/test_live_smoke.py](tests/cli/test_live_smoke.py) に `LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE` を使う opt-in smoke を追加し、`/v1/models` と exact alias `llmb-minimal-chat` を前提に suites -> run -> report を確認できるようにした。
- [tests/config/test_loader.py](tests/config/test_loader.py) と [tests/cli/test_main.py](tests/cli/test_main.py) を更新し、新しい suite / prompt set / model 解決を固定した。
- 関連テストは `python -m unittest tests.config.test_loader tests.cli.test_main tests.cli.test_live_smoke` で 30 tests, OK, skipped=6 を確認した。
- live run は LM Studio 実機ではなく fallback OpenAI-compatible endpoint で実施し、[manifest.json](tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/manifest.json) と [run-metrics.json](tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/run-metrics.json) に 3 records 完走の証跡を残した。

# 次アクション

- LM Studio 実機で `lms` が使える環境では、`LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke` を 1 回通し、exact alias 前提まで含めて実証する。
- 正式比較へ広げる場合は alias-backed readiness slot を流用せず、actual backing model ごとに model_key を分ける別 request を切る。
