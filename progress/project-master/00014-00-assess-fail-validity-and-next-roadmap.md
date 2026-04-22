---
request_id: "00014"
task_id: "00014-00"
parent_task_id:
owner: "project-master"
title: "assess-fail-validity-and-next-roadmap"
status: "done"
depends_on: []
child_task_ids:
  - "00014-01"
  - "00014-02"
  - "00014-03"
created_at: "2026-04-18T22:00:00+09:00"
updated_at: "2026-04-18T23:15:00+09:00"
related_paths:
  - "README.md"
  - "prompts/rewrite/polite-rewrite-v1.toml"
  - "prompts/constrained_generation/followup-action-json-v1.toml"
  - "prompts/extraction/invoice-fields-v1.toml"
  - "tmp/runtime-checks/request-00013-20260418-151043"
  - "progress/evaluation-analyst/00012-03-assess-current-evaluation-method.md"
  - "progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md"
  - "progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md"
  - "progress/reviewer/00014-03-review-fail-validity-and-roadmap.md"
---

# 入力要件

- Ollama 側の fail case を減らすために JSON 出力条件と required phrase 条件を見直すのが先ではないか確認したい。
- ただし fail を減らすこと自体が目的ではなく、fail 原因を整理したうえで結果の確からしさを検証したい。
- 現時点の結果を benchmark として問題ないと見なせるか判断したい。
- 残りのロードマップを整理し、残作業があるなら次を進めたい。

# 整理した要件

- 必須要件は、request 00013 の fail が prompt 条件どおりの妥当な fail か、過度に brittle な scorer 由来かを切り分けること。
- 必須要件は、現在の結果をどの範囲で「問題ない」と言えるかを、benchmark の目的に照らして明示すること。
- 必須要件は、README のロードマップと各 request の次アクションから未完了項目を抽出し、次に進める 1 件を決めること。
- 任意要件は、JSON-only と exact phrase を将来どう改善するかの方針を整理すること。

# 作業内容

- project-master が request 00013 の artifact、関連 prompt、README のロードマップを再確認した。
- fail 妥当性の判断を evaluation-analyst へ、prompt 契約の見直し観点を prompt-analyst へ、最終整合確認を reviewer へ委譲する。
- project-master は各既存 request の次アクションを統合し、次の着手候補を決める。
- evaluation-analyst は、fenced JSON fail と exact required phrase fail は strict contract benchmark として妥当だが、sentence_count は brittle なので強い主張の根拠にしない方がよいと整理した。
- prompt-analyst は、JSON-only と exact phrase は strict instruction-following prompt としては成立するが、general quality の代表にはしにくいため、将来は strict と tolerant を分けるべきだと整理した。
- reviewer は重大 finding なしと判断し、現在の結果は strict instruction-following benchmark としては問題なく、残ロードマップの主タスクは比較レポート整備でよいと確認した。

# 判断

- 現在の Ollama fail は、概ね scorer 偶発ではなく prompt 契約どおりの条件不一致として解釈してよい。
- invoice-fields-v1 と followup-action-json-v1 の fail は、strict machine-readable JSON gate を満たさなかったことを示しており、payload 自体の意味理解失敗とは切り分けて読むべきである。
- polite-rewrite-v1 の fail は exact required phrase 不一致を主根拠として読むのが妥当で、sentence_count は explainability caution に留めるべきである。
- よって現状結果は、strict machine-readable JSON と explicit lexical / structural constraint-following を測る benchmark としては問題ない。
- 一方で、semantic quality、自然な rewrite 品質、payload correctness と wrapper cleanliness の分離は未実装であり、これらを主張するのは現状では過剰である。
- README の 5 段ロードマップ上で未完了の主項目は比較レポート整備である。OpenAI-compatible 用 suite / smoke は provider 拡張の follow-up、strict / tolerant split は解釈改善の後続課題として扱うのが妥当である。

# 成果

- request 00014 の親記録を作成した。
- 現在の結果は「fail が少ないから良い」ではなく、「strict contract benchmark として fail 原因が説明可能である」という意味で妥当だと整理した。
- JSON-only と exact required phrase は現行 prompt 契約として有効だが、将来は strict 指標と tolerant 指標を分離した方が benchmark の意味を保ちやすいと整理した。
- 残ロードマップの主タスクを比較レポート整備と確定し、優先度を「比較レポート整備」「OpenAI-compatible suite / smoke」「strict / tolerant split」の順で整理した。

# 次アクション

- request 00015 として比較レポート整備を起票し、設計・実装・レビューへ委譲する。

# 関連パス

- README.md
- prompts/rewrite/polite-rewrite-v1.toml
- prompts/constrained_generation/followup-action-json-v1.toml
- tmp/runtime-checks/request-00013-20260418-151043