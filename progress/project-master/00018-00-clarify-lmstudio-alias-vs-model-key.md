---
request_id: "00018"
task_id: "00018-00"
parent_task_id: null
owner: "project-master"
title: "clarify-lmstudio-alias-vs-model-key"
status: "done"
depends_on: []
child_task_ids:
  - "00018-01"
  - "00018-02"
created_at: "2026-04-19T03:50:00+09:00"
updated_at: "2026-04-19T04:05:00+09:00"
related_paths:
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "progress/programmer/00018-01-clarify-lmstudio-alias-vs-model-key.md"
  - "progress/reviewer/00018-02-review-lmstudio-alias-vs-model-key.md"
---

# 要件整理

- `llmb-minimal-chat` が downloaded model key ではなく readiness 用 alias であることが分かりにくく、`lms load llmb-minimal-chat --identifier llmb-minimal-chat` が失敗した。
- config と docs の両方で、downloaded model key と API alias の違いを明示したい。

# 作業内容

- 関連 config と LM Studio docs を確認し、誤解の発生点を特定した。
- programmer に文言修正を委譲し、reviewer に最終確認を委譲する。
- programmer は readiness 用 config に alias コメントを追加し、LM Studio landing page と api-check に `lms ls` から始まる導線と正誤例を反映した。
- reviewer は重大 finding なしと判断し、landing page の最短確認にも `lms ls` を追加して、拾い読みでも次の一手が分かるように補強した。

# 判断

- 問題は runtime 実装ではなく、`provider_model_name = "llmb-minimal-chat"` が実モデル名に見える説明不足である。
- 今回は docs と config コメントの明確化だけで十分である。
- `llmb-minimal-chat` は downloaded model key ではなく readiness 用 API alias であり、`lms load` の第 1 引数には `lms ls` に出る downloaded model key を渡す必要がある。
- README は landing page、api-check は手順書、config は alias の意味を短く補足する、という責務分離で十分誤解を減らせる。

# 成果

- request 00018 を起票した。
- [configs/model_registry/openai-compatible-readiness.toml](configs/model_registry/openai-compatible-readiness.toml) に、`provider_model_name = "llmb-minimal-chat"` は downloaded model key ではなく readiness 用 alias だと分かるコメントを追加した。
- [docs/lmstudio/README.md](docs/lmstudio/README.md) に、`llmb-minimal-chat` は `lms ls` に出る downloaded model key ではなく、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` で作る alias だと追記した。
- [docs/lmstudio/api-check.md](docs/lmstudio/api-check.md) に、最初に `lms ls` を確認する手順と、`lms load llmb-minimal-chat --identifier llmb-minimal-chat` が誤りである正誤例を追加した。
- reviewer の軽微修正で、landing page の最短確認にも `lms ls` を追加した。

# 次アクション

- ユーザーは `lms ls` で downloaded model key を確認し、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` を実行すればよい。
- 将来 OpenAI-compatible readiness 導線を増やす場合は、alias、downloaded model key、API-visible 名の用語を 1 か所にまとめるとさらに分かりやすくなる。

