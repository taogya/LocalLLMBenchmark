---
request_id: "00018"
task_id: "00018-02"
parent_task_id: "00018-00"
owner: "reviewer"
title: "review-lmstudio-alias-vs-model-key"
status: "done"
depends_on:
  - "00018-01"
created_at: "2026-04-19T03:50:00+09:00"
updated_at: "2026-04-19T12:29:20+09:00"
related_paths:
  - "progress/project-master/00018-00-clarify-lmstudio-alias-vs-model-key.md"
  - "progress/programmer/00018-01-clarify-lmstudio-alias-vs-model-key.md"
  - "configs/model_registry/openai-compatible-readiness.toml"
  - "docs/lmstudio/README.md"
  - "docs/lmstudio/api-check.md"
---

# 入力要件

- alias と downloaded model key の違いが、config と docs で十分明確になっているか確認したい。

# 確認対象

- `progress/project-master/00018-00-clarify-lmstudio-alias-vs-model-key.md`
- `progress/programmer/00018-01-clarify-lmstudio-alias-vs-model-key.md`
- `configs/model_registry/openai-compatible-readiness.toml`
- `docs/lmstudio/README.md`
- `docs/lmstudio/api-check.md`

# 作業内容

- project-master と programmer の progress を読み、今回の意図が runtime 変更ではなく alias と downloaded model key の説明補強であることを確認した。
- config と LM Studio docs を読み、`provider_model_name = "llmb-minimal-chat"` の意味、`lms load` の正誤例、landing page と手順書の責務分離を点検した。
- 対象ファイルの diagnostics を確認し、今回の変更に起因する問題がないことを確認した。
- landing page の最短確認だけを読んだ利用者でも次に `lms ls` を実行すると分かるよう、`docs/lmstudio/README.md` に軽微修正を入れた。

# 発見事項

- 重大事項なし。`configs/model_registry/openai-compatible-readiness.toml` のコメント、`docs/lmstudio/README.md` の位置づけ説明、`docs/lmstudio/api-check.md` の手順 1 と正誤例がそろっており、`provider_model_name = "llmb-minimal-chat"` は downloaded model key ではなく readiness 用 alias だと読み取れる。
- 軽微事項あり。修正前の landing page は `<downloaded_model_key>` というプレースホルダ自体は出していたが、最短確認ブロックだけを拾い読みすると `lms ls` を先に見る流れが api-check ほど明確ではなかった。reviewer で `lms ls` を先頭に追加して補強した。

# 判断

- `lms load llmb-minimal-chat --identifier llmb-minimal-chat` が誤りであることは、`docs/lmstudio/api-check.md` の正誤例と補足文で十分明確である。
- README は landing page として入口の要約と詳細ページへの誘導に留まり、具体的な正誤判定や段階手順は api-check に置かれているため、README と api-check の責務分離は維持されている。
- 今回の軽微修正後は、landing page から入った利用者でも次の一手が `lms ls` で downloaded model key を確認することだと分かりやすい。

# 残課題

- なし。

# ユーザー報告可否

- 可。

# 改善提案

- 今後 OpenAI-compatible readiness 導線を増やす場合は、alias、downloaded model key、API-visible 名の用語を 1 か所に短く定義した共通メモを置くと、同種の誤解をさらに減らしやすい。

# 成果

- `llmb-minimal-chat` が readiness 用 alias であり、`lms load` の第 1 引数へ渡す downloaded model key ではないことを、config と docs の両方で確認した。
- `lms load llmb-minimal-chat --identifier llmb-minimal-chat` が誤りだと明確に読めることを確認した。
- landing page の最短確認にも `lms ls` を入れ、利用者の次アクションがより自然に分かる状態へ整えた。

# 次アクション

- project-master がこの review 結果を request 00018 の最終報告へ統合する。
