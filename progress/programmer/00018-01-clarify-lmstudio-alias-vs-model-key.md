---
request_id: "00018"
task_id: "00018-01"
parent_task_id: "00018-00"
owner: "programmer"
title: "clarify-lmstudio-alias-vs-model-key"
status: "done"
depends_on: []
created_at: "2026-04-19T03:50:00+09:00"
updated_at: "2026-04-19T12:27:29+09:00"
related_paths:
  - "progress/project-master/00018-00-clarify-lmstudio-alias-vs-model-key.md"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
---

# 入力要件

- `llmb-minimal-chat` は downloaded model key ではなく readiness 用 alias であることを、config と docs で誤解しにくくしたい。

# 作業内容

- `configs/model_registry/openai-compatible-readiness.toml` に、`provider_model_name = "llmb-minimal-chat"` が downloaded model key ではなく readiness 用 alias である短いコメントを追加した。
- `docs/lmstudio/README.md` に、`llmb-minimal-chat` は `lms ls` に出る downloaded model key ではなく、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` で作る API alias である説明を追記した。
- `docs/lmstudio/api-check.md` に、先に `lms ls` で downloaded model key を確認する手順と、`lms load llmb-minimal-chat --identifier llmb-minimal-chat` が誤りだと分かる補足を追加した。

# 判断

- 問題は runtime 実装ではなく alias と downloaded model key の役割の混同なので、public value は変更せずコメントと手順だけを補強した。
- README は landing page のまま要点だけを残し、誤りやすい操作例の説明は api-check に寄せた。

# 成果

- `llmb-minimal-chat` を `lms load` の第 1 引数に入れる誤用を、config コメントと LM Studio docs の両方で避けやすくした。
- 対象ファイルの diagnostics を確認し、今回の変更に起因する問題が出ていないことを確認した。

# 次アクション

- reviewer が文言の分かりやすさと責務分離を最終確認する。
