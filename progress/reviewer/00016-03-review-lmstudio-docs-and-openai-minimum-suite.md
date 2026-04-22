---
request_id: "00016"
task_id: "00016-03"
parent_task_id: "00016-00"
owner: "reviewer"
title: "review-lmstudio-docs-and-openai-minimum-suite"
status: "done"
depends_on:
  - "00016-02"
created_at: "2026-04-18T23:40:00+09:00"
updated_at: "2026-04-19T00:47:17+09:00"
related_paths:
  - "progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md"
  - "progress/solution-architect/00016-01-design-lmstudio-readiness-and-minimal-suite.md"
  - "progress/programmer/00016-02-implement-lmstudio-docs-and-openai-minimum-suite.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/lmstudio/README.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "configs/benchmark_suites/openai-compatible-minimal-v1.toml"
  - "configs/prompt_sets/minimal-readiness-ja-v1.toml"
  - "tests/config/test_loader.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_live_smoke.py"
  - "tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/manifest.json"
  - "tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/run-metrics.json"
---

# 入力要件

- LM Studio 導入文書、OpenAI-compatible minimal suite、live 検証、defer 判断が妥当か最終確認する。

# 作業内容

- progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md、progress/solution-architect/00016-01-design-lmstudio-readiness-and-minimal-suite.md、progress/programmer/00016-02-implement-lmstudio-docs-and-openai-minimum-suite.md を読み、設計意図と実装結果を照合した。
- README.md、docs/architecture/benchmark-foundation.md、docs/lmstudio/README.md、configs/provider_profiles/openai-compatible-local.toml、configs/model_registry/openai-compatible-readiness.toml、configs/prompt_sets/minimal-readiness-ja-v1.toml、configs/benchmark_suites/openai-compatible-minimal-v1.toml を確認し、readiness 専用導線と provider 非依存境界を点検した。
- tests/config/test_loader.py、tests/cli/test_main.py、tests/cli/test_live_smoke.py を確認し、suite 解決、CLI 表示、opt-in live smoke の責務が docs と一致するかを確認した。
- tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/manifest.json と run-metrics.json、加えて records.jsonl、raw/、一時 config root を確認し、fallback live run が LM Studio 実機証跡ではなく OpenAI-compatible 経路の疎通確認として読めるかを確認した。
- reviewer 側の軽微修正として、docs/lmstudio/README.md と README.md に readiness 専用 suite であること、`lms server start` と `lms load` を分けて扱うこと、fallback live run は LM Studio CLI の代替証跡ではないことを追記した。
- `get_errors` で README.md、docs/lmstudio/README.md、docs/architecture/benchmark-foundation.md、対象 config / tests の diagnostics 0 件を確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.config.test_loader tests.cli.test_main tests.cli.test_live_smoke` を実行し、30 tests, OK, skipped=6 を確認した。
- `command -v lms` は `lms:missing`、`curl -fsS http://localhost:1234/v1/models` は接続失敗、`curl -fsS http://localhost:11434/v1/models` は `llmb-minimal-chat:latest` を返すことを確認した。

# 判断

- LM Studio docs は、`lms server start` だけでは load されず、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` が別途必要であることを十分に明示している。reviewer 修正で、load 前に benchmark を実行すると alias 不在で失敗することも補足した。
- `openai-compatible-minimal-v1` は 1 model x 3 prompts の readiness 用最小 suite として妥当である。classification、strict JSON extraction、short_qa の 3 本に限定されており、README、architecture、LM Studio doc の 3 面で readiness 専用と読める状態になった。
- live smoke の exact alias `llmb-minimal-chat` 前提は、LM Studio 導線としては意図的に狭く、現時点では許容できる。`http://localhost:11434/v1/models` が `llmb-minimal-chat:latest` を返すため generic OpenAI-compatible smoke としてはやや brittle だが、programmer progress と docs で fallback live run を別扱いにしており、LM Studio readiness と OpenAI-compatible 経路確認の境界は保たれている。
- fallback live run の manifest.json と run-metrics.json は、`openai-compatible-minimal-v1` が OpenAI-compatible 経路で完走することの証跡としては妥当である。一方で LM Studio CLI の導入・load 手順を通した証跡ではないため、LM Studio 実機 readiness の代替にはならない。actual backing model は runtime artifact ではなく programmer progress に残っており、この読み分けは明示された状態である。
- strict / tolerant split と sentence_count explainability の defer は妥当である。今回の minimal suite は rewrite を含まず sentence_count heuristic に依存しないうえ、request 00014 で strict contract benchmark としての解釈範囲が既に整理されているため、今回の blocker ではない。
- docs / config / tests の追加は provider 非依存層の責務境界を壊していない。provider 固有の操作は docs と opt-in smoke に閉じ、common CLI、config loader、benchmark core へ LM Studio 固有 subcommand や hard-coded provider 名の help を持ち込んでいない。

# 成果

## 確認対象

- progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md
- progress/solution-architect/00016-01-design-lmstudio-readiness-and-minimal-suite.md
- progress/programmer/00016-02-implement-lmstudio-docs-and-openai-minimum-suite.md
- README.md
- docs/architecture/benchmark-foundation.md
- docs/lmstudio/README.md
- configs/provider_profiles/openai-compatible-local.toml
- configs/model_registry/openai-compatible-readiness.toml
- configs/prompt_sets/minimal-readiness-ja-v1.toml
- configs/benchmark_suites/openai-compatible-minimal-v1.toml
- tests/config/test_loader.py
- tests/cli/test_main.py
- tests/cli/test_live_smoke.py
- tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/manifest.json
- tmp/runtime-checks/request-00016-20260418-184120/results/request-00016-live-20260418-184120/run-metrics.json

## 発見事項

- 未解消の重大 finding はなし。
- 解消済み軽微事項: docs/lmstudio/README.md と README.md に、readiness 専用 suite であること、`lms server start` と `lms load` の分離、fallback live run の解釈境界を追記した。
- residual risk として、OpenAI-compatible live smoke は `/v1/models` に exact alias `llmb-minimal-chat` を要求するため、`llmb-minimal-chat:latest` のような tagged id を返す server にはそのままでは通らない。ただし現状は LM Studio 導線を狭く保つ意図と整合している。

## 残課題

- この環境では `lms` が未導入で、`http://localhost:1234/v1/models` も未起動のため、LM Studio 実機での opt-in live smoke は未確認である。
- runtime artifact 自体には actual backing model 名が残らないため、alias-backed readiness slot を正式比較へ流用するのは避けるべきである。現状は programmer progress の記録で補っている。
- generic OpenAI-compatible smoke として広げたくなった場合は、LM Studio 導線とは別 request で alias 正規化または provenance 表示の整理を行うのがよい。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、軽微な説明不足も reviewer 側で補強済みである。

## 改善提案

- LM Studio 実機で `LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke` を 1 回通し、`/v1/models` の exact alias 前提まで含めて実証するとよい。
- readiness を越えて比較用途へ広げる段階では、actual backing model 名を manifest か run metadata へ残す別 request を切ると、alias-backed slot の解釈が安定する。
- generic OpenAI-compatible server も smoke の対象に広げるなら、LM Studio 導線の opt-in smoke と分けて扱う方が責務境界を保ちやすい。

# 次アクション

- project-master へは、重大 finding なし、解消済み軽微事項あり、fallback live run は OpenAI-compatible 経路確認としてのみ解釈すべき、strict / tolerant split の defer は妥当、という結果を引き継げる。
