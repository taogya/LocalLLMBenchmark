---
request_id: "00019"
task_id: "00019-02"
parent_task_id: "00019-00"
owner: "reviewer"
title: "review-lmstudio-docs-actual-model-key"
status: "done"
depends_on:
  - "00019-01"
created_at: "2026-04-19T13:10:00+09:00"
updated_at: "2026-04-19T13:35:29+09:00"
related_paths:
  - "progress/project-master/00019-00-realign-lmstudio-docs-with-actual-model-keys.md"
  - "progress/programmer/00019-01-realign-lmstudio-docs-with-actual-model-keys.md"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "README.md"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
  - "docs/architecture/benchmark-foundation.md"
---

# 入力要件

- LM Studio docs が actual model key 中心へ寄り、一貫性の悪さが減ったか確認したい。

# 作業内容

- progress/project-master/00019-00-realign-lmstudio-docs-with-actual-model-keys.md と progress/programmer/00019-01-realign-lmstudio-docs-with-actual-model-keys.md を読み、今回の意図が「runtime は変えず docs と config コメントの重心だけを actual downloaded model key へ移すこと」だと確認した。
- configs/model_registry/openai-compatible-readiness.toml、README.md、docs/lmstudio/README.md、docs/lmstudio/api-check.md、docs/architecture/benchmark-foundation.md を確認し、actual key と alias の位置づけ、Ollama との一貫性、root docs の粒度を横断レビューした。
- `bonsai` の検索を user-facing docs と config に対して行い、壊れやすい固定例が残っていないことを確認した。
- get_errors で対象ファイルの diagnostics 0 件を確認した。
- 軽微な補強として docs/lmstudio/README.md の landing page に `lms load <downloaded_model_key>` を追記し、actual key をそのまま使う経路がコードブロックでも先に見えるようにした。
- reviewer shell から LM Studio CLI help の再確認も試したが、この shell では `lms` が PATH 上になく、help 出力の直接確認までは進められなかった。

# 判断

- 未解消の重大 finding はない。
- `lms get bonsai` のような固定語依存の例は user-facing docs から除去されており、壊れやすい具体例に引きずられる状態は解消している。
- actual downloaded model key を最初に `lms ls` で確定する流れは docs/lmstudio/api-check.md で明示され、README.md、docs/lmstudio/README.md、docs/architecture/benchmark-foundation.md も同じ読み方にそろっている。
- `llmb-minimal-chat` は actual key ではなく readiness alias slot だと一貫して書かれており、repo 同梱 config をそのまま使う互換 path に十分後退している。
- runtime を変えずに docs の重心だけを actual key へ移した判断は妥当である。Ollama の既定導線は維持され、LM Studio だけ actual key を自然な基準として読む補足を加える形に留まっている。
- README と architecture は LM Studio 固有詳細へ寄りすぎておらず、詳細手順は docs/lmstudio 配下へ押し込められている。

# 成果

## 確認対象

- progress/project-master/00019-00-realign-lmstudio-docs-with-actual-model-keys.md
- progress/programmer/00019-01-realign-lmstudio-docs-with-actual-model-keys.md
- configs/model_registry/openai-compatible-readiness.toml
- README.md
- docs/lmstudio/README.md
- docs/lmstudio/api-check.md
- docs/architecture/benchmark-foundation.md

## 発見事項

- 未解消の重大 finding はなし。
- 解消済み軽微事項: docs/lmstudio/README.md の landing page は本文で actual key 基準を説明していたが、最短確認のコマンド例が readiness 互換 path に寄って見えやすかったため、`lms load <downloaded_model_key>` を追記して主経路をコードブロックでも見えるように補強した。
- `bonsai` の検索ヒットは progress 記録と旧設計文脈のみで、README と docs 配下の user-facing 文書には残っていない。
- docs/lmstudio/api-check.md は `lms ls` -> `lms get <catalog-model-id>` / `lms get --always-show-all-results <search-term>` -> `lms load <downloaded_model_key>` の順で actual key route を先に置いており、alias route は compatibility path として明示されている。
- configs/model_registry/openai-compatible-readiness.toml のコメント、README.md、docs/architecture/benchmark-foundation.md の補足は、`llmb-minimal-chat` が readiness alias slot であるという説明に整合している。

## 残課題

- reviewer shell では `lms` が PATH 上になく、LM Studio CLI help をこの作業経路から直接再確認できなかった。今回の最終確認は、現行文書同士の整合と programmer 側の変更内容確認を主軸にしている。
- repo 同梱の openai-compatible-minimal-v1 は引き続き alias-backed な readiness suite であり、actual key をそのまま使う benchmark 運用は利用者側で別 model entry を持つ前提である。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、LM Studio docs は「actual downloaded model key が自然な基準」「`llmb-minimal-chat` は readiness 用の optional 互換 path」という読み方へ十分に寄ったと判断できる。

## 改善提案

- 今後、actual key ベースの OpenAI-compatible sample を repo 同梱で増やしたくなった場合は、alias の説明を戻すのではなく、actual key を `provider_model_name` に使う別 model entry / suite を追加する方が一貫性を保ちやすい。

# 次アクション

- project-master が本 review 結果を parent task へ統合し、重大 finding なし、軽微補強 1 件解消済みとしてユーザー報告へ進める。
