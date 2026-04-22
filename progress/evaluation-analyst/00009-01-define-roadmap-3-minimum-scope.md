---
request_id: "00009"
task_id: "00009-01"
parent_task_id: "00009-00"
owner: "evaluation-analyst"
title: "define-roadmap-3-minimum-scope"
status: "done"
depends_on: []
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T14:25:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "docs/architecture/benchmark-foundation.md"
  - "configs/prompt_sets/core-small-model-ja-v1.toml"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "src/local_llm_benchmark/storage/jsonl.py"
  - "prompts"
---

# 入力要件

- ロードマップ 3 の最小スコープと acceptance を定義したい。

# 整理した要件

- 改善提案 1〜3 がロードマップ 3 の最小スコープとして妥当かを、既存実装との差分ベースで評価する。
- deterministic scorer で end-to-end に比較可能になる範囲だけを固定する。
- case-evaluations.jsonl と run-metrics.json に最低限必要な項目を、実装とレビューに使える粒度で定義する。
- manual または hybrid 前提の scorer は今回の最小スコープから除外する。

# 作業内容

- README、architecture docs、prompt 定義、prompt set、evaluation 条件解決、JSONL ResultSink 実装を確認した。
- 現状の sample prompt は classification / extraction / rewrite の 3 件のみで、prompt set も 3 件だけを含むことを確認した。
- evaluation_reference は classification と extraction にはあるが、rewrite には未整備であり、summarization / short_qa / constrained_generation の prompt 自体も未実装であることを確認した。
- [src/local_llm_benchmark/benchmark/evaluation.py](src/local_llm_benchmark/benchmark/evaluation.py) では 6 カテゴリ分の deterministic evaluation.conditions が既に定義済みで、最小スコープの不足は prompt データ整備と評価結果出力に集中していることを確認した。
- [src/local_llm_benchmark/storage/jsonl.py](src/local_llm_benchmark/storage/jsonl.py) と [tests/storage/test_jsonl.py](tests/storage/test_jsonl.py) を確認し、現状の保存は manifest.json / records.jsonl / raw/ までで、case-evaluations.jsonl と run-metrics.json は未実装であることを確認した。
- request 00005 / 00006 の評価方針と照合し、similarity / rouge_like / factuality_check を今回の acceptance から外す方針を継続するのが妥当と判断した。

# 判断

- 改善提案 1〜3 は分割可能ではあるが、ロードマップ 3 の最小スコープとしては 3 つを一体で採用するのが妥当である。どれか 1 つでも欠けると、「同一条件で比較できる評価データをそろえる」という README 上のロードマップ 3 を完了扱いにできない。
- 今回固定するカテゴリと scorer の組み合わせは、evaluation.py に実装済みの deterministic 条件に合わせるのが最も安全である。
- evaluation_reference は全 prompt でセクションを持たせ、reference_type が label / text / json の prompt には scorer に必要な machine-readable 正解を必須とする。reference_type が none の prompt は空 object または補助情報のみでよい。
- case-evaluations.jsonl は 1 case x 1 metric の正本、run-metrics.json はその集計結果の正本とし、run-metrics は case-evaluations の再集計で再現できる粒度に留める。
- run-metrics の最小集計スコープは model_key x prompt_id とし、prompt_category を併記する。cross-run 比較、複数 prompt をまたいだ category 集計、manual 指標の混在保存は今回の最小スコープに含めない。

# 成果

## 最小スコープの結論

- ロードマップ 3 の最小スコープとして妥当なのは、改善提案 1〜3 をまとめて実施する案である。
- 具体的には、summarization / short_qa / constrained_generation の sample prompt 追加、全 sample prompt の evaluation_reference 整備、deterministic scorer に基づく case-evaluations.jsonl と run-metrics.json の出力実装までを 1 つの完了条件として扱う。
- 理由は、現状の [src/local_llm_benchmark/benchmark/evaluation.py](src/local_llm_benchmark/benchmark/evaluation.py) が 6 カテゴリ分の評価条件を持っている一方で、prompt corpus と結果出力がその境界まで追いついていないためである。今回埋めるべき差分は「カテゴリ実体化」「参照データ整備」「評価結果保存」の 3 点に集約される。

## 評価対象

- classification: exact_match_label v1 を case scorer とし、accuracy と macro_f1 を run metric とする。
- extraction: exact_match_json_fields v1 と json_valid v1 を case scorer とし、exact_match_rate と json_valid_rate を run metric とする。
- rewrite: constraint_pass v1 を case scorer とし、constraint_pass_rate を run metric とする。
- summarization: length_compliance v1 を case scorer とし、length_compliance_rate を run metric とする。
- short_qa: exact_match_text v1 を case scorer とし、exact_match_rate を run metric とする。
- constrained_generation: constraint_pass v1 と format_valid v1 を case scorer とし、constraint_pass_rate と format_valid_rate を run metric とする。

## 推奨条件または推奨指標

- prompt set の最小完成形は 6 カテゴリ各 1 prompt とし、[configs/prompt_sets/core-small-model-ja-v1.toml](configs/prompt_sets/core-small-model-ja-v1.toml) で 6 prompt_id を解決できる状態にする。
- 各 prompt は [src/local_llm_benchmark/benchmark/evaluation.py](src/local_llm_benchmark/benchmark/evaluation.py) の category ごとの conditions と矛盾しない evaluation_metadata を持つ。
- classification / extraction / short_qa は scorer が直接使う evaluation_reference を必須とする。
- rewrite / summarization / constrained_generation は output_contract を machine-readable に保ち、constraint_ids、required_phrases、forbidden_phrases、sentence_count、length_range、required_keys など deterministic 判定に必要な条件を明示する。
- json_valid_rate と format_valid_rate の run threshold は 1.0 を維持し、それ以外の run threshold は今回も未固定でよい。

## case-evaluations.jsonl の最低限必要な項目

- schema_version
- run_id
- case_id
- model_key
- prompt_id
- prompt_category
- metric_name
- scorer_name
- scorer_version
- reference_type
- evaluation_mode
- score
- passed
- normalized_prediction
- normalized_reference
- details

## run-metrics.json の最低限必要な項目

- schema_version
- run_id
- metrics
- 各 metric 要素の scope: model_key、prompt_id、prompt_category
- 各 metric 要素の metric_name
- 各 metric 要素の scorer_name
- 各 metric 要素の scorer_version
- 各 metric 要素の aggregation
- 各 metric 要素の value
- 各 metric 要素の threshold
- 各 metric 要素の passed
- 各 metric 要素の sample_count
- 各 metric 要素の evaluation_mode

## acceptance criteria

- prompts 配下に summarization / short_qa / constrained_generation の sample prompt が追加され、既存 3 prompt と合わせて 6 カテゴリ各 1 prompt がそろっている。
- [configs/prompt_sets/core-small-model-ja-v1.toml](configs/prompt_sets/core-small-model-ja-v1.toml) が 6 prompt_id を含み、最小スコープの prompt set として解決できる。
- 全 6 prompt が evaluation_metadata と output_contract を持ち、category と scorer の組み合わせが [src/local_llm_benchmark/benchmark/evaluation.py](src/local_llm_benchmark/benchmark/evaluation.py) の fixed deterministic 条件と一致する。
- 全 6 prompt が metadata.evaluation_reference セクションを持ち、reference_type が label / text / json の prompt では scorer が必要とする正解値を machine-readable に保持している。
- [src/local_llm_benchmark/storage/jsonl.py](src/local_llm_benchmark/storage/jsonl.py) 相当の保存処理が records.jsonl に加えて case-evaluations.jsonl と run-metrics.json を出力する。
- case-evaluations.jsonl は 1 case x 1 metric で 1 行を持ち、最低限必要な項目を満たす。normalized_reference は reference_type = none の場合に null を許容する。
- run-metrics.json は deterministic metric のみを対象とし、少なくとも model_key x prompt_id 単位で集計結果を保持する。prompt_category は各 metric 要素に併記される。
- extraction の失敗詳細では missing_fields または mismatched_fields、constraint 系では failed_constraints、format 系では format_errors、length 系では実測長を details に残せる。
- similarity / rouge_like / factuality_check は公式 metric として出力されず、case-evaluations.jsonl と run-metrics.json の対象外である。
- テストで 6 カテゴリの evaluation.conditions 解決、case-evaluations の行数と metric 名、run-metrics の主要キーが検証される。

## 根拠メモ

- [README.md](README.md) は 6 カテゴリの初期評価指標を既に掲げているが、現物の sample prompt と prompt set は 3 カテゴリに留まっている。
- [docs/architecture/prompt-and-config-design.md](docs/architecture/prompt-and-config-design.md) は deterministic scorer の固定範囲と manual / hybrid の除外範囲を既に整理しており、今回の最小スコープはその実装追従として位置づけるのが自然である。
- [docs/architecture/benchmark-foundation.md](docs/architecture/benchmark-foundation.md) は case-evaluations.jsonl と run-metrics.json を拡張境界として定義しており、今回の request はその境界を最小実装へ昇格させる作業にあたる。
- [src/local_llm_benchmark/storage/jsonl.py](src/local_llm_benchmark/storage/jsonl.py) は records.jsonl と raw/ の分離を既に満たしているため、今回の追加は保存責務の拡張として局所化しやすい。

## 未解決事項

- reference_type = none の prompt で metadata.evaluation_reference を空 object に統一するか、キー自体を持たせないかは実装側で最終決定が必要である。ただし最小スコープではセクションをそろえる方がレビューしやすい。
- run-metrics.json を model_key x prompt_id のみで始めるか、同時に model_key x prompt_category 集計も持たせるかは solution-architect 側で決めてよい。
- details の厳密なキー名は scorer 実装に合わせて最終化が必要だが、失敗原因が追える粒度は必須である。

## 改善提案

- case-evaluations.jsonl を run-metrics.json の単一入力とし、集計ロジックを二重管理しない構成にすると再現性が高い。
- manual / hybrid の scorer は同じファイルへ混在させず、将来追加する場合も evaluation_mode で明確に分離できる形を維持した方がよい。
- 新規 3 prompt には 1 件ずつゴールデンテストを用意し、prompt metadata と output_contract が scorer 前提を満たすかを固定しておくと、今後の prompt 改訂でも評価条件が崩れにくい。

# 次アクション

- prompt-analyst は 6 カテゴリ完成形に合わせて新規 3 prompt と evaluation_reference の具体値を定義する。
- solution-architect は本タスクの最小必須項目を基に case-evaluations.jsonl / run-metrics.json の保存スキーマ詳細を確定する。
- programmer は prompt 追加、prompt set 更新、結果出力実装、テスト追加を行う。
- reviewer は similarity / rouge_like / factuality_check が公式 acceptance へ混入していないかを重点確認する。

# 関連パス

- README.md
- docs/architecture/prompt-and-config-design.md
- src/local_llm_benchmark/benchmark/evaluation.py
- prompts