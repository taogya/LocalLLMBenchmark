---
request_id: "00012"
task_id: "00012-04"
parent_task_id: "00012-00"
owner: "reviewer"
title: "review-secret-handling-and-runtime-readiness"
status: "done"
depends_on:
  - "00012-02"
  - "00012-03"
created_at: "2026-04-18T19:20:00+09:00"
updated_at: "2026-04-18T14:36:01+09:00"
related_paths:
  - "progress/solution-architect/00012-01-design-secret-env-and-runtime-check.md"
  - "progress/programmer/00012-02-implement-secret-env-and-validate-runtime.md"
  - "progress/evaluation-analyst/00012-03-assess-current-evaluation-method.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/providers/factory.py"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/providers/test_factory.py"
  - "tests/config/test_loader.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_live_smoke.py"
---

# 入力要件

- secret handling の変更と runtime readiness の説明が妥当か確認したい。
- progress/reviewer/00012-04-review-secret-handling-and-runtime-readiness.md を done まで進めたい。

# 整理した要件

- 平文 api_key を repo の sample config 契約から排除できているかを確認する。
- `api_key_env` 未指定時の keyless 契約と、指定済み未解決時の fail fast が実装、docs、tests で一致しているかを確認する。
- provider 非依存境界、README / architecture docs の readiness 説明、現行評価方式とランダム性説明、最低限の回帰テストと実行確認結果を横断レビューする。
- 軽微な整合修正だけ reviewer で扱い、重大 finding がなければその旨を明示する。

# 作業内容

- progress/solution-architect/00012-01-design-secret-env-and-runtime-check.md、progress/programmer/00012-02-implement-secret-env-and-validate-runtime.md、progress/evaluation-analyst/00012-03-assess-current-evaluation-method.md を読み、設計意図、実装内容、評価説明の前提を照合した。
- configs/provider_profiles/openai-compatible-local.toml、src/local_llm_benchmark/providers/factory.py、README.md、docs/architecture/benchmark-foundation.md、docs/architecture/prompt-and-config-design.md、src/local_llm_benchmark/benchmark/evaluation.py、tests/providers/test_factory.py、tests/config/test_loader.py、tests/cli/test_main.py、tests/cli/test_live_smoke.py を確認した。
- `api_key_env|api_key` の検索で、sample profile には平文 `api_key` が残っておらず、factory は `connection.api_key` を reject、`connection.api_key_env` だけを解決することを確認した。
- `openai_compatible|OpenAI-compatible` の検索で、provider 固有語が provider 非依存層である cli、config、benchmark、registry、prompts、storage に流入していないことを確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.providers.test_factory tests.config.test_loader tests.cli.test_main tests.benchmark.test_evaluation` を再実行し、21 tests, OK を確認した。
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_live_smoke -v` を実行し、opt-in smoke が既定では 3 skip になることを確認した。
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v` を実行し、現環境では Ollama API 未起動のため setUpClass skip になることを確認した。
- `source .venv/bin/activate && local-llm-benchmark suites --config-root configs` と `source .venv/bin/activate && local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs` を実行し、code readiness 導線が README 記載どおり通ることを確認した。
- `source .venv/bin/activate && local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id reviewer-00012-runtime-20260418 --output-dir tmp/reviewer-results` を実行し、18 records の計画生成と artifact 保存までは成功し、Ollama API 未起動のため全件 `Connection refused` で止まることを確認した。
- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/reviewer-results/reviewer-00012-runtime-20260418` を実行し、`records: 18`、`metric_rows: 0`、`sample_count` と `record_count` の意味差 note を確認した。
- `curl -fsS http://localhost:1234/v1/models` を実行し、OpenAI-compatible local server は `localhost:1234` で未起動であることを確認した。

# 判断

- 平文 api_key を repo の sample config に残さない契約は守られている。sample profile は `api_key_env` のコメント例だけを持ち、factory は旧 `connection.api_key` を hard reject するため、repo に置かれた provider profile をそのまま共有しても secret 値は含まれない。
- `api_key_env` 未指定時の keyless 契約と、指定済み未解決時の fail fast は妥当である。tests/providers/test_factory.py で keyless 正常系、env 解決正常系、未設定 error、旧 `api_key` reject が固定されており、factory 実装とも一致している。
- provider 非依存境界は崩れていない。OpenAI-compatible 固有処理は providers/factory.py と providers/openai_compatible 配下に閉じ込められており、cli、config、benchmark、registry、prompts、storage に provider 固有語や暗黙 fallback は見当たらない。
- README と architecture docs の readiness 説明は、今回の実測結果と整合している。`suites` 系は code readiness として通り、`run` は environment readiness 不足時に `Connection refused` で止まり、`report` は scored case が 0 件であることを正しく表示する。
- 現行評価方式とランダム性の説明に大きな誤解はない。README と docs は deterministic scorer だけが公式 auto 評価であること、`json_valid_rate` / `format_valid_rate` の位置づけ、`seed` の provider 依存性、OpenAI-compatible v1 が `seed` を送らないことを、実装と整合する形で説明している。
- 最低限の回帰として、secret 契約の unit test と CLI / evaluation の unit test は十分である。一方で OpenAI-compatible local server の success-path は現環境で未確認であり、runtime readiness の最終判断は contract-level と error-path までに留まる。

# 成果

## 確認対象

- progress/solution-architect/00012-01-design-secret-env-and-runtime-check.md
- progress/programmer/00012-02-implement-secret-env-and-validate-runtime.md
- progress/evaluation-analyst/00012-03-assess-current-evaluation-method.md
- configs/provider_profiles/openai-compatible-local.toml
- src/local_llm_benchmark/providers/factory.py
- README.md
- docs/architecture/benchmark-foundation.md
- docs/architecture/prompt-and-config-design.md
- tests/providers/test_factory.py
- tests/config/test_loader.py
- tests/cli/test_main.py
- tests/cli/test_live_smoke.py
- src/local_llm_benchmark/benchmark/evaluation.py

## 発見事項

- 未解消の重大 finding はなし。
- reviewer によるコードまたは文書の修正は不要と判断した。progress 更新のみ実施した。

## 残課題

- OpenAI-compatible local server の success-path は現環境で未確認である。`curl http://localhost:1234/v1/models` は接続失敗で、auth 有無を含む runtime readiness は unit test と contract 確認までに留まる。
- 現行 sample suite と live smoke は Ollama 経路のみを通すため、OpenAI-compatible の keyless / `api_key_env` 契約を CLI end-to-end で回帰検知する smoke はまだない。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、request 00012 の secret handling と docs 説明は done として扱ってよい。報告時は、environment readiness の success-path が未確認である点だけ前提として添えるのが妥当である。

## 改善提案

- 次 request で OpenAI-compatible model を参照する最小 suite か、base_url / api_key_env を環境変数で差し替える opt-in smoke を 1 本追加すると、keyless と fail fast の契約を CLI 経路でも固定しやすい。
- OpenAI-compatible runtime readiness を README でさらに明確化したくなった場合は、既定 suite が Ollama 用であることと、OpenAI-compatible を試すには model registry 側に `provider_id = "openai_compatible"` の model を含む suite が必要であることを、別 request で短く補足すると誤読を減らせる。

# 検証

- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.providers.test_factory tests.config.test_loader tests.cli.test_main tests.benchmark.test_evaluation`
  - 21 tests, OK
- `source .venv/bin/activate && PYTHONPATH=src python -m unittest tests.cli.test_live_smoke -v`
  - 3 tests, OK, skipped=3
- `source .venv/bin/activate && PYTHONPATH=src LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke -v`
  - setUpClass skip: Ollama API に接続できません
- `source .venv/bin/activate && local-llm-benchmark suites --config-root configs`
  - suite 一覧の表示に成功
- `source .venv/bin/activate && local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs`
  - suite detail と required model identifier の表示に成功
- `source .venv/bin/activate && local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id reviewer-00012-runtime-20260418 --output-dir tmp/reviewer-results`
  - 18 records の計画生成と artifact 保存に成功、Ollama API 未起動のため 18 件すべて `Connection refused`
- `source .venv/bin/activate && local-llm-benchmark report --run-dir tmp/reviewer-results/reviewer-00012-runtime-20260418`
  - `records: 18`、`metric_rows: 0`、scope mismatch note を確認
- `curl -fsS http://localhost:1234/v1/models`
  - `localhost:1234` へ接続できず、OpenAI-compatible local server 未起動を確認

# 次アクション

- project-master へ、重大 finding なし、追加修正なし、unit test と code readiness 確認成功、environment readiness success-path は未確認という結果を引き継ぐ。

# 関連パス

- README.md
- src/local_llm_benchmark/providers/factory.py
- src/local_llm_benchmark/benchmark/evaluation.py