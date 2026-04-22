---
request_id: "00017"
task_id: "00017-00"
parent_task_id: null
owner: "project-master"
title: "assess-provider-loading-policy-and-harmonize-docs"
status: "done"
depends_on: []
child_task_ids:
  - "00017-01"
  - "00017-02"
  - "00017-03"
created_at: "2026-04-19T01:05:00+09:00"
updated_at: "2026-04-19T03:40:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/ollama/README.md"
  - "docs/ollama/api-check.md"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "configs/provider_profiles/local-default.toml"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/providers/ollama/adapter.py"
  - "src/local_llm_benchmark/providers/ollama/client.py"
  - "src/local_llm_benchmark/providers/openai_compatible/client.py"
  - "src/local_llm_benchmark/benchmark/runner.py"
  - "progress/solution-architect/00017-01-design-provider-loading-policy-and-doc-harmonization.md"
  - "progress/programmer/00017-02-update-provider-operation-docs.md"
  - "progress/reviewer/00017-03-review-provider-operation-docs.md"
---

# 要件整理

- Ollama と LM Studio のロード挙動を公式仕様と現行コードの組み合わせで確認し、現状の運用が妥当かを検証する。
- 多モデル時のメモリ滞留リスクがどこから来るかを整理し、今の構成に問題があるなら、その性質と回避方針を明示する。
- docs/ollama と docs/lmstudio の構成差を見直し、構成と見出しの統一方針を決める。
- 処理を複雑化しない前提で、必要なら docs / config 方針を更新する。

# 作業内容

- Ollama keep_alive と LM Studio JIT loading / TTL / Auto-Evict の一次情報を確認した。
- 現行 adapter / runner / provider profile と provider docs の差分を整理した。
- 設計、実装、最終確認を各 agent へ委譲する。
- solution-architect は、Ollama を client-driven residency、LM Studio を server-driven dynamic loading と読み分け、LM Studio の alias 手動 load は readiness 専用に限定すべきと整理した。
- programmer は docs のみを更新し、README、architecture、provider docs を統一見出しへ寄せたうえで、LM Studio README を landing page 化し、手順を [docs/lmstudio/api-check.md](docs/lmstudio/api-check.md) へ分離した。
- reviewer は重大 finding なしと判断し、運用評価と docs 構成統一が妥当であることを確認した。progress timestamp の逆転も補正した。

# 判断

- 現時点では code の複雑化より、現挙動の整理と推奨運用の明文化が先である。
- LM Studio は alias 手動 load だけが唯一の運用ではなく、JIT loading を含めて再評価が必要である。
- Ollama の keep_alive=5m は prompt 群の連続実行には都合がよい一方、多モデル時の滞留リスクを持つため、その位置づけを整理する必要がある。
- 現行 runner は逐次実行であり、メモリ問題は benchmark 側の並列性ではなく provider 側の residency policy から生じる。
- Ollama の keep_alive = "5m" は baseline 向け latency 寄り default としては維持可能だが、低メモリや多 model 切替の一般推奨とは読ませない方がよい。
- LM Studio の明示 alias load は readiness 用 explicit path としては有効だが、一般 benchmark では JIT loading、Idle TTL、Auto-Evict の既定動作で読む方が自然である。
- 今回は docs 更新だけで十分であり、provider-specific unload hook、LM Studio 固有 API 連携、ttl 送信、config schema 変更は不要である。

# 成果

- request 00017 を起票した。
- [docs/ollama/README.md](docs/ollama/README.md) と [docs/lmstudio/README.md](docs/lmstudio/README.md) を、provider の位置づけ、ロード政策の要約、readiness と benchmark の読み分け、最短確認、詳細ページ、公式参照先、という同じ landing page 構成へそろえた。
- [docs/ollama/api-check.md](docs/ollama/api-check.md) に、CLI 経路で `keep_alive = "5m"` が送られることと、`load_duration` が reload 観測点になることを追記した。
- [docs/lmstudio/api-check.md](docs/lmstudio/api-check.md) を新設し、`lms get` -> `lms server start` -> `lms load --identifier llmb-minimal-chat` -> `/v1/models` -> minimal suite 実行、の readiness 手順を README から分離した。
- [README.md](README.md) と [docs/architecture/benchmark-foundation.md](docs/architecture/benchmark-foundation.md) に、benchmark core は load/unload を自動化せず、Ollama は keep_alive、LM Studio は JIT / TTL / Auto-Evict を provider 側の政策として読む、という cross-provider 方針を反映した。
- source code と config schema は変更していない。今回の結論は docs だけで十分だった。

# 次アクション

- 低メモリ環境での実運用判断をさらに助けたい場合は、後続 request で Ollama の `keep_alive` を短くする例や `0` にする例を provider docs へ追加する。
- LM Studio を readiness から正式 multi-model benchmark へ広げる場合は、alias slot ではなく actual model identifier を持つ config と provenance の整理を別 request で扱う。
