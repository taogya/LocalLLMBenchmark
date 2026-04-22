---
request_id: "00012"
task_id: "00012-00"
parent_task_id:
owner: "project-master"
title: "secure-provider-secrets-and-runtime-validation"
status: "done"
depends_on: []
child_task_ids:
  - "00012-01"
  - "00012-02"
  - "00012-03"
  - "00012-04"
created_at: "2026-04-18T19:20:00+09:00"
updated_at: "2026-04-18T20:45:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/config"
  - "src/local_llm_benchmark/providers"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "tests/config"
  - "tests/providers"
  - "tests/cli"
---

# 入力要件

- OpenAI-compatible local server 用 profile の API キーを config 平文で持たせるのは危険なので、必要なら環境変数名参照へ改めたい。
- すでに安全設計なら運用方法を文書化したい。
- 現状の構成で実際に benchmark を動かせる状態か確認したい。
- 完走性、評価レポートの妥当性、ランダム性に対する評価手法、現在の評価アルゴリズムを整理したい。

# 整理した要件

- まず profile と factory の現状を確認し、秘密情報を平文保持しているなら環境変数参照へ切り替える。
- 実装変更が入る場合は README と sample profile も更新し、運用方法を明示する。
- 実行可能性は unit test と可能なら live smoke / sample run で確認し、実環境依存の前提も明示する。
- 評価方式は deterministic scorer の現状、乱数影響の扱い、未採用の類似度系手法を切り分けて説明する。

# 作業内容

- 現状確認の結果、`configs/provider_profiles/openai-compatible-local.toml` に `api_key` の平文例があり、`src/local_llm_benchmark/providers/factory.py` も `connection.api_key` をそのまま client へ渡していることを確認した。
- 子タスクとして、秘密情報設計、実装と runtime 検証、評価手法整理、レビューを委譲する。
- 設計アーキテクトが、OpenAI-compatible local server の secret 契約を `connection.api_key_env` に寄せ、未指定なら keyless、指定済みで未解決なら fail fast、loader ではなく provider factory でだけ解決する方針を整理した。
- programmer が sample profile、provider factory、README、architecture doc、関連 tests を更新し、平文 `api_key` を repo から外した。
- programmer が unit test と CLI 実行で runtime verification を試行し、`suites` と suite detail は成功、`run` は artifact 保存と 18 records の計画生成までは成功、Ollama 未起動のため全件 `Connection refused`、`report` は failure artifact を正常に読めることを確認した。
- 評価アナリストが、現行評価は 7 つの deterministic scorer とその run 集計だけで、レーベンシュタイン、ROUGE-like、embedding 類似度、LLM judge、manual / hybrid は公式 auto 評価へ含めていないこと、乱数影響を統計的に吸収する仕組みは未実装であることを整理した。
- reviewer が secret handling、provider 非依存境界、README / docs、評価方式説明、検証結果を横断確認し、重大 findings なしと判断した。

# 判断

- この profile は local server 用の sample でも、平文 API キー例を残すより環境変数名参照へ寄せた方が安全で、README でも誤用を防ぎやすい。
- 実行可能性の確認は、コード上の readiness と実際の環境 readiness を分けて扱う必要がある。前者は unit / smoke で確認し、後者はローカルの server 起動と model 配備に依存する。
- 現時点で確認できたのは code readiness までで、environment readiness は未達である。CLI、config、artifact、report surface は動くが、現環境では Ollama と OpenAI-compatible local server が未起動で success-path の完走確認までは到達していない。
- 現行の公式評価は deterministic metric 中心であり、単発 run の完走性、形式妥当性、制約遵守の確認には使えるが、semantic quality と stochastic robustness の評価にはまだ不十分である。

# 成果

- request 00012 の親記録を作成した。
- `configs/provider_profiles/openai-compatible-local.toml` は keyless 既定へ変更し、認証が必要な場合だけ `connection.api_key_env` で環境変数名を指定する運用へ切り替えた。
- `src/local_llm_benchmark/providers/factory.py` は OpenAI-compatible local server 向けに、旧 `connection.api_key` を reject、`connection.api_key_env` のみを解決、未指定なら Authorization header なし、指定済み未解決なら fail fast するようにした。
- README と `docs/architecture/benchmark-foundation.md` に、secret 運用、code readiness / environment readiness の切り分け、OpenAI-compatible local server の auth 契約を追記した。
- 現行評価方式とランダム性の限界を README と `docs/architecture/prompt-and-config-design.md` に反映し、レーベンシュタインや類似度系が未採用であること、複数回実行や分散集計が未実装であることを明示した。
- 検証として、unit test 23 件成功、diagnostics 0 件、`suites` / suite detail 成功、`run` の artifact 保存成功、`report` の failure artifact 読込成功を確認した。
- 最終判断として、code readiness は確認済み、environment readiness は Ollama と OpenAI-compatible local server の未起動により未達である。

# 次アクション

- Ollama を起動し、README 記載相当の `suites -> run -> report` success-path を再実行して environment readiness を確認する。
- OpenAI-compatible local server を `localhost:1234/v1` で起動し、keyless と `api_key_env` ありの両方で実疎通を確認する。
- 次段で OpenAI-compatible provider 用の opt-in smoke か最小 suite を追加すると、今回の secret 契約を CLI 経路でも固定しやすい。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- docs/architecture/prompt-and-config-design.md
- configs/provider_profiles/openai-compatible-local.toml
- src/local_llm_benchmark/providers/factory.py
- src/local_llm_benchmark/benchmark/evaluation.py