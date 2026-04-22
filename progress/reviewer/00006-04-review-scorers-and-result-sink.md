---
request_id: "00006"
task_id: "00006-04"
parent_task_id: "00006-00"
owner: "reviewer"
title: "review-scorers-and-result-sink"
status: "done"
depends_on:
  - "00006-03"
created_at: "2026-04-18T00:20:00+09:00"
updated_at: "2026-04-17T22:47:37+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "configs/model_registry/local-models-v1.toml"
  - "prompts"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "src/local_llm_benchmark/storage"
  - "tests"
  - "tmp/reviewer-results/reviewer-00006-smoke"
---

# 入力要件

- README のモデル取得方針、scorer 定義と閾値、ResultSink 実装を最終確認する。

# 整理した要件

- README の説明が利用者に分かりやすいこと。
- 保存実装が設計と整合し、必要な評価条件を追跡できること。
- tests と docs がコードと整合していること。

# 作業内容

- README のモデル取得方針を確認し、このパッケージがモデル自動ダウンロードを行わず、provider 側で事前取得する前提が README 単体で分かることを確認した。
- configs/benchmark_suites/local-three-tier-baseline-v1.toml と configs/model_registry/local-models-v1.toml を照合し、README の pull 例が sample suite の 3 モデルと一致することを確認した。
- docs/architecture/prompt-and-config-design.md、prompts 配下 3 件、src/local_llm_benchmark/benchmark/evaluation.py、src/local_llm_benchmark/benchmark/runner.py を確認し、fixed scorer、threshold、evaluation.conditions、reference snapshot の内容が整合していることを確認した。
- src/local_llm_benchmark/storage/jsonl.py、docs/architecture/benchmark-foundation.md、tests/storage/test_jsonl.py を確認し、raw response と normalized records の分離、request_snapshot.evaluation.conditions の保存、manifest の plan snapshot 保存を確認した。
- 軽微な整合修正として、JsonlResultSink が既存 run_id の結果ディレクトリへ追記して records.jsonl と raw/ を混在させる余地を防ぐガードを追加し、normalized records から provider_metadata を外して raw 側へ寄せた。あわせて docs とテストを最小更新した。
- get_errors で変更ファイルの診断 0 件を確認した。
- `PYTHONPATH=src .venv/bin/python -m unittest tests.benchmark.test_runner tests.storage.test_jsonl tests.cli.test_main tests.config.test_loader tests.prompts.test_repository tests.providers.test_ollama_adapter` を実行し、12 tests 成功を確認した。
- `PYTHONPATH=src .venv/bin/python -m local_llm_benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id reviewer-00006-smoke --output-dir tmp/reviewer-results` を実行し、Ollama 未起動のため 9 件すべて Connection refused で終了する一方、manifest.json と records.jsonl が生成され、classification / extraction / rewrite の evaluation.conditions と閾値が保存されることを確認した。

# 判断

- README だけで「モデルは自動ダウンロードしない」「provider 側で事前取得する」「sample suite のモデル名は何か」が分かる粒度になっている。
- sample suite の explicit_model_keys と model registry の provider_model_name、README の pull 例は一致しており、利用者が事前取得対象を誤読しにくい。
- scorer 定義と閾値は README、docs、prompt metadata、request snapshot の 4 点で整合している。classification は accuracy / macro_f1、extraction は exact_match_rate / json_valid_rate、rewrite は constraint_pass_rate として一貫している。
- ResultSink は raw response と normalized records を分離し、request_snapshot.evaluation.conditions、reference_snapshot、output_contract_snapshot を records 側へ保存できている。
- provider 依存情報は、normalized records では provider_id と provider_model_name を request_snapshot に留め、provider_metadata は raw 側へ退避したため、設計意図により近い状態になった。
- 実 Ollama 環境での成功系 E2E は未確認だが、現行環境で docs と unit test と error-path の実ファイル保存までは確認できている。

# 成果

- 確認対象:
  - README.md
  - docs/architecture/benchmark-foundation.md
  - docs/architecture/prompt-and-config-design.md
  - configs/benchmark_suites/local-three-tier-baseline-v1.toml
  - configs/model_registry/local-models-v1.toml
  - prompts/classification/contact-routing-v1.toml
  - prompts/extraction/invoice-fields-v1.toml
  - prompts/rewrite/polite-rewrite-v1.toml
  - src/local_llm_benchmark/benchmark/evaluation.py
  - src/local_llm_benchmark/benchmark/runner.py
  - src/local_llm_benchmark/storage/jsonl.py
  - src/local_llm_benchmark/cli/main.py
  - tests/benchmark/test_runner.py
  - tests/storage/test_jsonl.py
  - tests/cli/test_main.py
- 発見事項:
  - 解消済み軽微事項: JsonlResultSink が既存 run_id のディレクトリへ追記できる状態だったため、run_id 再利用時に結果が混在しないようガードを追加した。
  - 解消済み軽微事項: normalized records に provider_metadata を保持しており、benchmark-foundation.md の「records 側の provider 依存情報は provider_id と provider_model_name までに留める」という記述とずれていたため、provider_metadata は raw 側へ寄せ、docs とテストを最小更新した。
  - 未解消の重大 finding はなし。
- 残課題:
  - 実 Ollama サーバーが起動し、README にある 3 モデルが pull 済みの環境での成功系 E2E は未確認。
  - sample prompt は現時点で classification、extraction、rewrite の 3 カテゴリのみで、summarization、short_qa、constrained_generation は docs 上の fixed 定義までに留まる。
- ユーザー報告可否:
  - 可能。重大ブロッカーはなく、成功系の実 API 実行未確認だけ前提として添えればよい。
- 改善提案:
  - provider 利用可能な環境で、README の最小実行をそのまま叩く成功系 smoke を 1 本追加すると、モデル取得方針と ResultSink の実運用確認を継続しやすい。
  - 将来 case-evaluations.jsonl と run-metrics.json を実装するときは、今回保存した evaluation.conditions と 1 対 1 に対応する回帰テストを先に置くと差分追跡が容易になる。

# 次アクション

- project-master へ、重大 finding なし、軽微な整合修正 2 件をレビュー時に解消済み、12 tests 成功、実 CLI の error-path 保存確認済みという結果を引き継ぐ。

# 関連パス

- README.md
- src/local_llm_benchmark/storage
- tests
- docs/architecture