---
request_id: "00014"
task_id: "00014-03"
parent_task_id: "00014-00"
owner: "reviewer"
title: "review-fail-validity-and-roadmap"
status: "done"
depends_on:
  - "00014-01"
  - "00014-02"
created_at: "2026-04-18T22:00:00+09:00"
updated_at: "2026-04-18T17:42:00+09:00"
related_paths:
  - "progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md"
  - "progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md"
  - "progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md"
  - "README.md"
  - "tmp/runtime-checks/request-00013-20260418-151043"
---

# 入力要件

- evaluation-analyst と prompt-analyst の判断が、benchmark の目的と README のロードマップと整合するか確認する。
- 現在の結果を問題ないと説明できるか、次に着手すべき残ロードマップが妥当か確認する。
- 最低限、1) strict instruction-following benchmark として統合してよいか、2) sentence_count に過剰な主張が混ざっていないか、3) 残ロードマップの主タスクを比較レポート整備としてよいか、4) OpenAI-compatible suite / smoke と strict / tolerant split の優先度を確認する。

# 整理した要件

- progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md、progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md、progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md、README.md、tmp/runtime-checks/request-00013-20260418-151043 を相互照合し、strict benchmark としての解釈範囲を確認する。
- runtime artifact と scorer 実装の一次情報から、JSON fail と rewrite fail が scorer 偶発ではなく契約違反として読めるかを確認する。
- sentence_count は raw artifact で説明可能か、少なくとも project-master が統合時に言い過ぎない状態かを確認する。
- README の残ロードマップと project の目的から、次の主タスクと follow-up の優先度を整理する。

# 作業内容

- progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md、progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md、progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md、README.md を確認した。
- tmp/runtime-checks/request-00013-20260418-151043 の manifest.json、run-metrics.json、records.jsonl、case-evaluations.jsonl、raw/ を確認した。
- raw/00002-local.entry.gemma3-invoice-fields-v1.json と raw/00012-local.balanced.qwen2_5-followup-action-json-v1.json で、fail case が fenced JSON 由来であることを確認した。
- raw/00003-local.entry.gemma3-polite-rewrite-v1.json と records.jsonl で、gemma3 の polite-rewrite-v1 は見た目上 1 文の応答である一方、case-evaluations.jsonl では observed_sentence_count = 2 になっていることを再確認した。
- src/local_llm_benchmark/benchmark/evaluation.py を確認し、JSON 系は raw json.loads をそのまま使い、rewrite は required_phrase と sentence_count の deterministic 判定で採点していることを確認した。
- README のロードマップで、未完了の主項目が 5. 比較レポート整備であり、4. provider 拡張は着手済みのままであることを確認した。

# 判断

## 1. 現在の結果を strict instruction-following benchmark として統合してよいか

- 統合してよい。現状の fail は、raw JSON-only、required_keys / required_values、exact required phrase、1 文制約といった明示契約にモデル出力が一致しなかった結果として読める。
- ただし統合時の表現は限定すべきである。問題ないと言えるのは、strict machine-readable JSON と explicit lexical / structural constraint-following を測る benchmark としてであり、抽出品質や自然な rewrite 品質全般まで保証する意味ではない。
- progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md と progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md は、この射程を守っており、benchmark の目的との整合は取れている。

## 2. sentence_count に過剰な主張が混ざっていないか

- evaluation-analyst と prompt-analyst の記録は、sentence_count を brittle な heuristic として扱っており、現状でも過剰主張は抑えられている。
- 一方で project-master が統合時に sentence_count を強い根拠として前面化するのは避けるべきである。raw artifact 上の gemma3 polite-rewrite-v1 は見た目上 1 文であり、case-evaluations.jsonl の observed_sentence_count = 2 は artifact 単体で説明し切れない。
- したがって、gemma3 rewrite fail の妥当性は required_phrase 不一致だけで十分に支えられる、と統合した方が安全である。sentence_count は「追加の explainability gap がある」「将来の scorer 説明性改善候補である」に留めるのが妥当である。

## 3. 残ロードマップの主タスクを比較レポート整備としてよいか

- よい。README の残ロードマップ上で未完了の主項目は 5. 比較レポート整備であり、project の主目的である「ベンチマークを取得し、比較し、蓄積すること」に最も直結している。
- request 00014 の妥当性整理により、現在の strict 指標を strict 指標として読む前提は固まったため、残ロードマップの主タスクを比較レポート整備とする判断は benchmark の目的と整合する。
- ただし比較レポート側では、現在の指標が strict gate であることを README と同じ粒度で明示した方がよい。strict fail をそのまま semantic quality fail と誤読させないためである。

## 4. OpenAI-compatible suite / smoke と strict / tolerant split の優先度

- 優先度は、1) 比較レポート整備、2) OpenAI-compatible suite / smoke、3) strict / tolerant split、の順が妥当である。
- 比較レポート整備が最優先なのは、現在すでに保存されている結果を定常的な比較フローへ載せることが project の主目的に最も近いためである。
- OpenAI-compatible suite / smoke は次点が妥当である。project は特定 provider 固定を避ける方針であり、現在は Ollama の success-path しか end-to-end で確認できていないため、比較対象を provider-neutral に広げる価値が高い。
- strict / tolerant split は重要だが、現行 strict benchmark 自体の妥当性は今回確認できたため、直近の blocker ではない。strict 指標の意味を report で明示したうえで、後続の interpretability 改善として進める位置付けが適切である。
- なお sentence_count の再確認は strict / tolerant split 全体の前提というより、scorer explainability の小タスクとして切り出す方がよい。残ロードマップの主見出しに置くほどの粒度ではない。

# 成果

## 確認対象

- progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md
- progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md
- progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md
- README.md
- tmp/runtime-checks/request-00013-20260418-151043/manifest.json
- tmp/runtime-checks/request-00013-20260418-151043/run-metrics.json
- tmp/runtime-checks/request-00013-20260418-151043/records.jsonl
- tmp/runtime-checks/request-00013-20260418-151043/case-evaluations.jsonl
- tmp/runtime-checks/request-00013-20260418-151043/raw/00002-local.entry.gemma3-invoice-fields-v1.json
- tmp/runtime-checks/request-00013-20260418-151043/raw/00003-local.entry.gemma3-polite-rewrite-v1.json
- tmp/runtime-checks/request-00013-20260418-151043/raw/00012-local.balanced.qwen2_5-followup-action-json-v1.json
- src/local_llm_benchmark/benchmark/evaluation.py

## 発見事項

- 未解消の重大 finding はなし。
- 現在の結果は strict instruction-following benchmark として統合してよいが、strict machine-readable JSON と explicit lexical / structural constraint-following の範囲に限定して説明する必要がある。
- sentence_count は過剰主張の根拠にすべきではない。gemma3 polite-rewrite-v1 の fail 妥当性は required_phrase 不一致だけで十分であり、observed_sentence_count = 2 は explainability caution として扱うのが妥当である。
- 残ロードマップの主タスクを比較レポート整備とする判断は README と project 目的に整合している。

## 残課題

- OpenAI-compatible provider には adapter 実装があるが、benchmark suite / live smoke の end-to-end 経路はまだ未整備である。
- strict / tolerant split は未実装であり、wrapper cleanliness と payload correctness、lexical contract と tolerant quality の分離は将来課題のままである。
- sentence_count の explainability はなお弱く、必要なら raw artifact と scorer 再現 test を使った限定的な切り分けが別途必要である。

## ユーザー報告可否

- 可能。重大なブロッカーはなく、request 00014 の最終確認としては done と扱ってよい。

## 改善提案

- 比較レポート整備では、現在の metric が strict gate であることを表示面でも明示し、semantic quality の代理指標として誤読されないようにした方がよい。
- その次の request では、OpenAI-compatible model を含む最小 suite か opt-in smoke を追加し、provider-neutral comparison の土台を固めるとよい。
- strict / tolerant split を進める場合は、sentence_count の単独改善ではなく、JSON wrapper と payload correctness、rewrite lexical constraint と tolerant quality を分ける設計としてまとめて扱う方がよい。

# 次アクション

- project-master は以下を親記録へ統合できる。
  - 重大 finding なし。
  - 現在の結果は strict instruction-following benchmark としては問題ない。
  - sentence_count は強い根拠にせず、required_phrase 不一致を主根拠にする。
  - 残ロードマップの主タスクは比較レポート整備でよい。
  - follow-up 優先度は、比較レポート整備、OpenAI-compatible suite / smoke、strict / tolerant split の順が妥当である。

# 次アクション

- 依存タスク完了後に最終確認を記録する。