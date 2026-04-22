# API 疎通確認

このページは、LM Studio と `openai-compatible-minimal-v1` の readiness を確認する手順です。まず actual downloaded model key を確定し、その後に repo 同梱 readiness slot をそのまま使うかどうかを選びます。`llmb-minimal-chat` は optional な compatibility alias であり、actual key そのものではありません。

## 前提

- `lms` は LM Studio に同梱される CLI です。追加インストールは不要です。
- `lms` を使う前に、LM Studio 本体を一度起動してください。
- benchmark core は model の load/unload を自動化しません。

## 1. actual downloaded model key を確認する

```bash
lms ls
```

`lms ls` に出る名前が actual downloaded model key です。benchmark で provider model identifier を考えるときも、まずこの値を基準に読みます。`llmb-minimal-chat` はここに出る key ではなく、後段で `--identifier` に渡す readiness 用 alias です。

## 2. model を未取得なら取得する

```bash
lms get <catalog-model-id>

# broad term しか分からない場合は検索結果から選ぶ
lms get --always-show-all-results <search-term>

lms ls
```

`lms get` は catalog model id で直接取得できます。broad term しか分からない場合は `--always-show-all-results` を付け、候補から actual match を選んでください。取得後に `lms ls` を見て、次の `lms load` に渡す actual downloaded model key を確定します。

## 3. server を起動する

```bash
lms server start
```

`lms server start` は HTTP server を起動するだけで、model load までは行いません。

## 4. model を load する

推奨: actual model key をそのまま使う

```bash
lms load <downloaded_model_key>
```

LM Studio を自然に読むならこちらです。正式比較や provider 間の一貫性を優先する場合は、config 側でも actual downloaded model key を `provider_model_name` に合わせる方が分かりやすくなります。

readiness 互換: repo 同梱 slot をそのまま使う

```bash
lms load <downloaded_model_key> --identifier llmb-minimal-chat
```

`openai-compatible-minimal-v1` と `configs/model_registry/openai-compatible-readiness.toml` を repo 同梱のまま使う場合だけ、この compatibility path を選びます。`llmb-minimal-chat` 自体を第 1 引数へ渡すのは誤りです。この alias は readiness 用に API-visible 名を固定するためのもので、一般 benchmark の標準運用ではありません。

## 5. OpenAI-compatible endpoint を確認する

```bash
curl http://localhost:1234/v1/models
```

actual model key route なら actual key が見えていれば十分です。readiness 互換 route を選んだ場合は `llmb-minimal-chat` も見えることを確認してください。

## 6. minimal suite を実行する

```bash
local-llm-benchmark suites openai-compatible-minimal-v1 --config-root configs
local-llm-benchmark run --config-root configs --suite openai-compatible-minimal-v1
```

`openai-compatible-minimal-v1` は readiness 用の最小 suite です。repo 同梱 config を変更せずに使う場合は、手順 4 の readiness 互換 route で `llmb-minimal-chat` alias を出しておいてください。actual key ベースで運用する場合は、自分の config 側の `provider_model_name` を actual downloaded model key に合わせます。

## 7. 補足

- このページは explicit alias load を使う readiness 導線です。
- このページは、まず actual downloaded model key を確定し、その後で readiness 互換 alias を必要なときだけ足す二段構えで読んでください。
- 一般 benchmark では、LM Studio の JIT loading、Idle TTL、Auto-Evict の既定動作を前提に読みます。
- alias を load せずに readiness suite を実行すると、`llmb-minimal-chat` 不在として失敗します。