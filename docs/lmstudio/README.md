# LM Studio

このディレクトリは、LM Studio を OpenAI-compatible provider として使うときの landing page です。入口だけをここに置き、詳細手順は下位ページへ分けます。

## provider の位置づけ

- LM Studio はこのリポジトリでは `openai_compatible` provider profile 経由で使います。
- benchmark core は model の download、load、pin、unload を自動化しません。
- LM Studio では `lms ls` に出る actual downloaded model key を provider model identifier の基準として読むのが自然です。
- 現行 docs では readiness 確認と benchmark 運用を分けて案内します。

## ロード政策の要約

- LM Studio server の既定は JIT loading enabled です。
- JIT loaded model の Idle TTL 既定値は 60 minutes です。
- Auto-Evict は既定で enabled です。
- 現行 client は `ttl` を送らないため、benchmark 側は LM Studio の server-driven policy をそのまま使います。

## readiness と benchmark の読み分け

- `llmb-minimal-chat` は actual downloaded model key ではなく、repo 同梱の `openai-compatible-minimal-v1` をそのまま試すときだけ使う readiness 用 API alias です。
- alias 固定は repo 同梱 readiness slot の互換 path であり、一般 benchmark の推奨運用ではありません。
- provider 間の一貫性を優先する場合は、actual downloaded model key を `provider_model_name` に使う model entry を別に持つ方が自然です。
- benchmark の既定導線は JIT loading、Idle TTL、Auto-Evict を前提に読みます。

## 最短確認

model を取得済みでも、まず `lms ls` で actual downloaded model key を確認してください。actual key をそのまま使うのが基準で、repo 同梱 readiness slot をそのまま使う場合だけ、その key に `--identifier llmb-minimal-chat` を付けます。actual key を基準にした読み方と readiness 互換 path の違いは詳細ページで説明します。

```bash
lms ls
lms server start
# actual key をそのまま使う場合
lms load <downloaded_model_key>
# repo 同梱 readiness slot をそのまま使う場合だけ
lms load <downloaded_model_key> --identifier llmb-minimal-chat
curl http://localhost:1234/v1/models
local-llm-benchmark suites openai-compatible-minimal-v1 --config-root configs
local-llm-benchmark run --config-root configs --suite openai-compatible-minimal-v1
```

## 詳細ページ

- [api-check.md](api-check.md)

## 公式参照先

- LM Studio CLI: https://lmstudio.ai/docs/cli
- LM Studio Idle TTL and Auto-Evict: https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- LM Studio OpenAI-compatible `/v1/models`: https://lmstudio.ai/docs/developer/openai-compat/models