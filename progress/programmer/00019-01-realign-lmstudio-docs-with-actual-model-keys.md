---
request_id: "00019"
task_id: "00019-01"
parent_task_id: "00019-00"
owner: "programmer"
title: "realign-lmstudio-docs-with-actual-model-keys"
status: "done"
depends_on: []
created_at: "2026-04-19T13:10:00+09:00"
updated_at: "2026-04-19T13:30:00+09:00"
related_paths:
  - "progress/project-master/00019-00-realign-lmstudio-docs-with-actual-model-keys.md"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "README.md"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "docs/architecture/benchmark-foundation.md"
---

# 要件整理

- LM Studio docs を actual downloaded model key 中心に寄せ、alias は readiness 用の任意手段だと明確にする。
- `lms get bonsai` のような固定例は外し、現行 CLI に合う一般形へ置き換える。
- runtime と public config value `llmb-minimal-chat` 自体は変えず、docs とコメントだけで一貫性を補強する。

# 作業内容

- `docs/lmstudio/api-check.md` から固定例 `lms get bonsai` を外し、公式 CLI に合わせて `lms get <catalog-model-id>` と `lms get --always-show-all-results <search-term>` を使う形へ更新した。
- `docs/lmstudio/api-check.md` を、`lms ls` で actual downloaded model key を確定する流れから始め、`lms load <downloaded_model_key>` を推奨経路、`lms load <downloaded_model_key> --identifier llmb-minimal-chat` を repo 同梱 readiness slot の互換経路として書き分けた。
- `docs/lmstudio/README.md` を actual downloaded model key 基準へ寄せ、`llmb-minimal-chat` は `openai-compatible-minimal-v1` をそのまま試すときだけ使う readiness alias slot だと明記した。
- `configs/model_registry/openai-compatible-readiness.toml` のコメントを補強し、repo 同梱 readiness slot であることと、一貫性重視なら actual downloaded model key を使う別 model entry へ寄せられることを追記した。
- `README.md` と `docs/architecture/benchmark-foundation.md` は短い補足だけに留め、generic な `model alias` という表現を `model identifier` へ寄せつつ、LM Studio は actual downloaded model key を自然な基準に読むと補足した。
- `get_errors` で変更対象 5 ファイルの diagnostics 0 件を確認した。

# 判断

- 問題の根本は runtime ではなく docs の重心だったため、public config value は維持し、actual key を先に確定する読み方だけを強めた。
- landing page と手順書の責務は維持し、詳細な二段構えは `docs/lmstudio/api-check.md` に寄せた。
- repo 同梱 `openai-compatible-minimal-v1` を変更せずに試す導線だけが alias 必須であり、一般 benchmark や provider 間の一貫性は actual downloaded model key 基準で読む方が自然だと整理した。

# 成果

- LM Studio docs は `lms ls` で actual downloaded model key を確認する流れが先頭に来るようになり、`llmb-minimal-chat` は optional な readiness compatibility alias として読めるようになった。
- 固定語 `bonsai` に依存した `lms get` 例を削除し、存在しない可能性がある具体語に引きずられない書き方へ統一した。
- 変更対象の diagnostics は 0 件だった。

# 次アクション

- reviewer が project-master 統合前に、LM Studio docs と root docs の用語整合を最終確認する。
