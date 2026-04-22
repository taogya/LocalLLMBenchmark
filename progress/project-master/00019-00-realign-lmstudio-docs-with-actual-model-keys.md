---
request_id: "00019"
task_id: "00019-00"
parent_task_id: null
owner: "project-master"
title: "realign-lmstudio-docs-with-actual-model-keys"
status: "done"
depends_on: []
child_task_ids:
  - "00019-01"
  - "00019-02"
created_at: "2026-04-19T13:10:00+09:00"
updated_at: "2026-04-19T13:45:00+09:00"
related_paths:
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "README.md"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/programmer/00019-01-realign-lmstudio-docs-with-actual-model-keys.md"
  - "progress/reviewer/00019-02-review-lmstudio-docs-actual-model-key.md"
---

# 要件整理

- `lms get bonsai` の例が実際の CLI で失敗し、docs の取得例が不正確である。
- Ollama は実モデル名ベースなのに LM Studio だけ alias ベースに見え、一貫性が悪い。
- 実装を複雑化せず、LM Studio docs を actual model key 中心へ寄せ、alias を readiness 用の任意手段として位置づけ直したい。

# 作業内容

- LM Studio docs と readiness config の現状を確認した。
- programmer に docs / コメント補正を委譲し、reviewer に最終確認を委譲する。
- programmer は LM Studio docs と config コメントの重心を actual downloaded model key 側へ移し、`lms get bonsai` のような固定例を除去した。
- reviewer は重大 finding なしと判断し、landing page の最短確認にも actual key をそのまま load する経路を補強した。

# 判断

- runtime 変更ではなく、docs と config コメントの重心を actual downloaded model key へ移すのが最小で妥当である。
- LM Studio の自然な読み方は `lms ls` に出る actual downloaded model key を基準にすることであり、`llmb-minimal-chat` は repo 同梱 readiness slot をそのまま使うときだけの optional alias path として下げるのが妥当である。
- Ollama との一貫性は runtime ではなく docs の重心で回復できる。provider 実装を増やさずとも、actual provider model name を基準に読む説明へ寄せれば十分である。

# 成果

- request 00019 を起票した。
- [docs/lmstudio/api-check.md](docs/lmstudio/api-check.md) から `lms get bonsai` を除去し、`lms get <catalog-model-id>` と `lms get --always-show-all-results <search-term>` の一般形へ置き換えた。
- [docs/lmstudio/api-check.md](docs/lmstudio/api-check.md) は `lms ls` で actual downloaded model key を確定し、`lms load <downloaded_model_key>` を推奨、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` を readiness 互換 path として書き分ける形へ更新した。
- [docs/lmstudio/README.md](docs/lmstudio/README.md)、[README.md](README.md)、[docs/architecture/benchmark-foundation.md](docs/architecture/benchmark-foundation.md) は、LM Studio では actual downloaded model key を自然な基準として読み、`llmb-minimal-chat` は optional な readiness alias slot だと分かる表現へ更新した。
- [configs/model_registry/openai-compatible-readiness.toml](configs/model_registry/openai-compatible-readiness.toml) のコメントを補強し、repo 同梱 readiness slot であることと、一貫性重視なら actual key ベースの model entry へ寄せられることを明記した。

# 次アクション

- ユーザーはまず `lms ls` で chat / instruct model の actual downloaded model key を確認し、その key を `lms load` の第 1 引数に渡す。
- repo 同梱の readiness suite をそのまま使う場合だけ、`--identifier llmb-minimal-chat` を付ける。
