# configs/ サンプル一式

`local-llm-benchmark` を初めて使うユーザー向けの最小サンプルです。中心目的 (あなたの PC・用途で最適なローカルモデルを選ぶ) を実演するための最小素材であり、本番運用では各自の環境に合わせて差し替えてください。

## ディレクトリ構成

```
configs/
  task_profiles/
    qa-basic.toml          # Task Profile 1 件
  model_candidates.toml    # Model Candidate 1 件
  providers.toml           # Provider 設定 (Ollama)
  run.toml                 # Run 設定
  run-alt.toml             # 同モデル違い条件 (compare 用 2 つ目)
  comparison.toml          # Comparison 設定 (run_id を後で書き換える)
```

## 前提

- `ollama serve` が起動済み (既定の `http://localhost:11434`)
- 本サンプルでは `qwen2.5:7b` を `ollama pull qwen2.5:7b` 済みであること

## 最短手順

`--store-root` に渡したディレクトリは自動生成されるため、事前に `mkdir` する必要はありません。以下の例では作業ディレクトリ直下の `./results` を結果保存先として使います。

```sh
# 設定検証
local-llm-benchmark check --config-dir configs --store-root ./results

# 1 Run 目: temperature=0.0
local-llm-benchmark run --config-dir configs --run-config configs/run.toml \
    --store-root ./results

# 2 Run 目: temperature=0.7 (compare 用)
local-llm-benchmark run --config-dir configs --run-config configs/run-alt.toml \
    --store-root ./results

# 過去 Run 一覧
local-llm-benchmark runs --store-root ./results

# 2 Run を束ねて Comparison
local-llm-benchmark compare --store-root ./results \
    --run-id <RUN_ID_A> --run-id <RUN_ID_B>

# Markdown レポート
local-llm-benchmark report --store-root ./results --comparison-id <COMP_ID>
```
