---
request_id: "00004"
task_id: "00004-02"
parent_task_id: "00004-00"
owner: "programmer"
title: "implement-config-externalization"
status: "done"
depends_on:
  - "00004-01"
created_at: "2026-04-17T22:25:00+09:00"
updated_at: "2026-04-17T23:58:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark"
  - "tests"
  - ".github/instructions/python-benchmark.instructions.md"
  - "configs"
  - "prompts"
---

# 入力要件

- provider 非依存ファイルから `Ollama` 固有表現を減らし、必要な箇所へ閉じ込める。
- ロードマップ 1 の config 外部化を実装する。
- 3 ランク各 1 モデルの初期比較条件を外部設定で表現できるようにする。
- 必要ならルール化をファイルへ反映する。

# 整理した要件

- 設計結果に従って config loader、設定ファイル、CLI、テスト、README を更新する。
- 既存の provider adapter 境界を壊さない。
- ルール化する場合は .github 配下の責務に沿った場所へ限定して追記する。

# 作業内容

- config/models.py と config/loader.py を TOML ベースの共通設定スキーマと loader に置き換え、benchmark_suites、model_registry、prompt_sets、provider_profiles、prompts を外部ファイルから読むようにした。
- providers/factory.py を追加し、provider 組み立てを providers 配下へ寄せた。共通 CLI は provider 固有 import とサブコマンドを持たない run コマンドだけに整理した。
- configs 配下に 3 ランク各 1 モデルの sample config を追加し、prompts 配下に初期比較用の prompt 定義を追加した。
- README と docs/architecture、docs/ollama を現行 CLI と config root 構成に合わせて更新した。
- tests/config/test_loader.py を追加し、tests/cli/test_main.py と tests/benchmark/test_runner.py を更新した。

# 判断

- 外部設定形式は YAML ではなく TOML を採用した。理由は、Python 3.13 の stdlib にある tomllib で依存追加なしに読めること、今回の最小スコープでは構造が十分表現できること、手編集と diff の見通しがよいことの 3 点。
- config root は `configs` を基本にしつつ、sample 構成では sibling の `prompts` も自動解決するようにした。これで CLI は `--config-root configs` のまま使え、設計メモの契約も保ちやすい。
- provider 固有診断コマンドは request 00004 の最小スコープ外として削り、必要な provider 組み立てだけを factory に残した。

# 成果

- `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1` で、外部設定から 3 モデル × 3 prompt の実行計画まで到達する共通 CLI を実装した。
- provider 非依存ファイルである cli/main.py と config/*.py から Ollama 固有コマンド、help 文言、stub 既定値を除去した。
- loader 正常系、loader 異常系、generic CLI、3 モデル解決の単体テストを追加または更新した。

# 次アクション

- reviewer へ最終確認を依頼する。
- 必要なら provider_profiles の profile_id 化や ResultSink 実装を次 request で進める。

# 関連パス

- README.md
- src/local_llm_benchmark
- tests
- .github/instructions/python-benchmark.instructions.md