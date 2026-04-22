---
request_id: "00017"
task_id: "00017-02"
parent_task_id: "00017-00"
owner: "programmer"
title: "update-provider-operation-docs"
status: "done"
depends_on:
  - "00017-01"
created_at: "2026-04-19T01:05:00+09:00"
updated_at: "2026-04-19T03:23:27+09:00"
related_paths:
  - "progress/project-master/00017-00-assess-provider-loading-policy-and-harmonize-docs.md"
  - "progress/solution-architect/00017-01-design-provider-loading-policy-and-doc-harmonization.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/ollama/README.md"
  - "docs/ollama/api-check.md"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "configs/provider_profiles/local-default.toml"
---

# 入力要件

- 設計結果に基づき、provider の運用方針と docs 構成を統一的に更新する。

# 作業内容

- `docs/ollama/README.md` を landing page として整理し、provider の位置づけ、`keep_alive` ベースのロード政策、readiness と benchmark の読み分け、詳細ページ導線を追加した。
- `docs/ollama/api-check.md` に、CLI 経路で `local-default.toml` の `keep_alive = "5m"` が送られることと、`load_duration` が reload 観測点になることを追記した。
- `docs/lmstudio/README.md` を単独手順書から landing page へ作り替え、JIT loading、Idle TTL、Auto-Evict を既定政策として整理した。
- `docs/lmstudio/api-check.md` を新規追加し、`lms get` -> `lms server start` -> `lms load --identifier llmb-minimal-chat` -> `/v1/models` -> minimal suite 実行、の readiness 手順を移した。
- `README.md` と `docs/architecture/benchmark-foundation.md` に、benchmark core は load/unload を自動化しないという cross-provider 方針を短く追記した。

# 判断

- provider README は landing page と index に寄せ、provider 固有の実行手順は subpage に逃がす構成で統一した。
- LM Studio の `llmb-minimal-chat` alias は readiness 専用の explicit path として残し、一般 benchmark の推奨運用とは切り分けた。
- Ollama の `keep_alive = "5m"` は config 変更ではなく文書補足で位置づけを整理し、low-memory 一般推奨と誤読されにくい形にした。

# 成果

- Ollama と LM Studio の provider docs を同じ見出し構成へそろえた。
- LM Studio README の役割を index に変更し、詳細手順を `docs/lmstudio/api-check.md` に分離した。
- root README と architecture doc に、逐次 runner と provider 委譲のロード方針を反映した。

# 次アクション

- reviewer が README、architecture、provider docs の責務境界と文言整合を最終確認する。
