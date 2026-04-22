# API 疎通確認

task_id 00001-03 の最小確認手順です。まずは curl、次にこのリポジトリの Python 基盤コードで確認します。

## 1. API バージョン確認

```bash
curl http://localhost:11434/api/version
```

期待値は JSON です。

```json
{"version":"0.x.y"}
```

## 2. ローカルモデル一覧確認

```bash
curl http://localhost:11434/api/tags
```

モデル未取得なら `models` が空でも構いません。まずは HTTP 200 と JSON が返ることを見ます。

## 3. chat API の最小確認

Ollama の API Reference では、`POST /api/chat` に `stream: false` を付けると単一 JSON 応答になります。

```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:latest",
    "messages": [
      {
        "role": "user",
        "content": "短く『接続成功』と返してください。"
      }
    ],
    "stream": false
  }'
```

`message.content` に応答本文が入れば、モデル呼び出しまで通っています。

## 4. このリポジトリの CLI で benchmark 経路確認

request 00004 以降の共通 CLI は provider 固有サブコマンドを持ちません。sample config では `configs/provider_profiles/local-default.toml` にある接続設定を使って Ollama adapter を組み立てます。

```bash
local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 --run-id ollama-smoke-00004
```

成功時は、少なくとも次の情報が出ます。

- run_id
- suite_id
- records
- success / errors
- model_key ごとの要約行

このコマンドは次の経路を確認します。

1. external config loader が `configs/*` と sibling の `prompts/*` を読む
2. runner が suite -> model -> prompt を解決する
3. providers.factory が provider profile から adapter を組み立てる
4. Ollama adapter が provider 固有 payload を作る
5. Ollama client が `/api/chat` を呼ぶ

この CLI 経路では、`configs/provider_profiles/local-default.toml` の `keep_alive = "5m"` が `/api/chat` に送られます。baseline 向けの連続実行では妥当ですが、低メモリ環境では長めです。

## 5. `load_duration` の見方

Ollama の chat response には `load_duration` が含まれます。model 切替や unload 後の再実行で reload cost を見たいときは、この値を観測点にします。

## 6. opt-in live smoke

README の `suites` -> `run` 導線をまとめて確認したい場合は、Ollama 起動済みかつ sample suite の 3 モデル取得済みの前提で次を実行します。

```bash
LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke
```

この smoke は `suites --config-root configs`、`suites local-three-tier-baseline-v1 --config-root configs`、`run --config-root configs --suite local-three-tier-baseline-v1 --run-id ... --output-dir ...` を順に確認し、Ollama 未起動や必要モデル不足なら skip 理由を表示します。

## 7. 失敗時の切り分け

- `Connection refused` 系なら Ollama が起動していない可能性が高いので、`ollama serve` または GUI 起動状態を確認する
- `model not found` 系なら `ollama pull gemma3:latest` のように先に取得する
- CLI だけ失敗するなら、仮想環境有効化と `python -m pip install -e .`、`configs/provider_profiles/local-default.toml` の接続先を見直す
