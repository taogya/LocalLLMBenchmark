---
request_id: "00004"
task_id: "00004-03"
parent_task_id: "00004-00"
owner: "reviewer"
title: "review-provider-neutral-config"
status: "done"
depends_on:
  - "00004-02"
created_at: "2026-04-17T22:25:00+09:00"
updated_at: "2026-04-17T21:06:35+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark"
  - "tests"
  - ".github/instructions/python-benchmark.instructions.md"
---

# 入力要件

- provider 非依存境界の修正と config 外部化の結果を最終確認する。

# 整理した要件

- provider 固有語が不適切なファイルへ漏れていないか確認する。
- config 外部化が README のロードマップ 1 に対応する粒度まで進んでいるか確認する。
- 3 ランク各 1 モデルの初期設定が説明とコードで整合しているか確認する。

# 作業内容

- provider 非依存層である cli/main.py、config/*.py、benchmark/*.py、registry/*.py、prompts/*.py、storage/*.py に対して `ollama|Ollama` と sample suite/model/prompt ID の検索を行い、対象層に provider 固有語や既定 ID の埋め込みが残っていないことを確認した。
- README、docs/architecture/prompt-and-config-design.md、docs/ollama 配下を確認し、request 00004 で定義した generic CLI 契約、config root 構成、3 ランク baseline suite の説明が現行実装と整合していることを確認した。
- configs/benchmark_suites/local-three-tier-baseline-v1.toml、configs/model_registry/local-models-v1.toml、configs/prompt_sets/core-small-model-ja-v1.toml、configs/provider_profiles/local-default.toml、prompts 配下の sample prompt を確認し、3 ランク各 1 モデルと 3 prompt の baseline 構成が外部設定で表現されていることを確認した。
- get_errors を全体に対して実行し、診断 0 件を再確認した。
- `PYTHONPATH=src .venv/bin/python -m unittest tests.config.test_loader tests.cli.test_main tests.benchmark.test_runner tests.prompts.test_repository tests.providers.test_ollama_adapter` を実行し、レビュー時点で 9 tests 成功を確認した。
- `PYTHONPATH=src .venv/bin/python -m local_llm_benchmark run --config-root configs --suite local-three-tier-baseline-v1` を実行し、9 件の実行計画まで到達し、実環境では Ollama 未起動のため全件 Connection refused で終了することを確認した。構造としては external config -> generic CLI -> provider factory -> runner の経路が通っている。
- 小さな整合修正として、config loader の duplicate ID エラーで先頭ファイルのパスが欠落する不具合を src/local_llm_benchmark/config/loader.py で修正し、tests/config/test_loader.py に回帰テストを追加した。

# 判断

- provider 非依存境界の観点では、確認対象の共通層に Ollama 固有 import、help 文言、サブコマンド、sample ID の埋め込みは見当たらず、provider 固有実装は providers/factory.py と providers/ollama 配下へ閉じ込められていると判断した。
- README のロードマップ 1 は、外部 TOML 設定、generic CLI、sample baseline suite、関連 unit tests がそろっているため、request 00004 の最小スコープでは「実装済み」と扱ってよい。
- generic CLI の実ランタイム確認は Ollama サーバー未起動のため成功までは未確認だが、9 レコードの計画生成と provider adapter 呼び出し経路までは現行環境で確認できており、構造要件は満たしている。
- duplicate ID 時のエラー表示はレビュー時点で軽微な不整合だったが、影響範囲が小さく root cause が明確だったため reviewer で最小修正して閉じた。

# 成果

- 確認対象:
  - README.md
  - docs/architecture/prompt-and-config-design.md
  - docs/ollama/README.md
  - docs/ollama/api-check.md
  - src/local_llm_benchmark/cli/main.py
  - src/local_llm_benchmark/config/models.py
  - src/local_llm_benchmark/config/loader.py
  - src/local_llm_benchmark/benchmark/runner.py
  - src/local_llm_benchmark/registry/model_registry.py
  - src/local_llm_benchmark/prompts/repository.py
  - src/local_llm_benchmark/storage/stub.py
  - src/local_llm_benchmark/providers/factory.py
  - configs
  - prompts
  - tests/config/test_loader.py
  - tests/cli/test_main.py
  - tests/benchmark/test_runner.py
- 発見事項:
  - 解消済みの軽微事項: config loader の duplicate ID エラーが先頭ファイルのパスを正しく含まないため、src/local_llm_benchmark/config/loader.py を最小修正し、tests/config/test_loader.py に回帰テストを追加した。
  - 未解消の重大 finding はなし。
- 残課題:
  - 実 Ollama サーバーと対象 3 モデルが起動・取得済みの環境での成功系実行は未確認。
  - provider profile は現状 provider_id 単位のため、同一 provider の複数接続先を同時に扱う要件が出た場合は profile_id 導入が必要。
- ユーザー報告可否:
  - 可能。重大なブロッカーはなく、成功系の実 API 検証未実施だけ前提として添えればよい。
- 改善提案:
  - 次 request では ResultSink 実装と合わせて、成功系の E2E smoke を 1 本持つと README の最小実行を継続検証しやすい。
  - provider profile を provider_id 直結から profile_id に拡張できる余地を docs に短く残しておくと、次の provider 拡張時の再設計が減る。

# 次アクション

- project-master へ、重大 finding なし、9 tests 成功、generic CLI の構造確認済み、実 Ollama 成功系は未確認という結果を引き継ぐ。

# 関連パス

- README.md
- src/local_llm_benchmark
- tests
- .github/instructions/python-benchmark.instructions.md