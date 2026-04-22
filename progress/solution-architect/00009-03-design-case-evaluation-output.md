---
request_id: "00009"
task_id: "00009-03"
parent_task_id: "00009-00"
owner: "solution-architect"
title: "design-case-evaluation-output"
status: "done"
depends_on:
  - "00009-01"
created_at: "2026-04-18T13:35:00+09:00"
updated_at: "2026-04-18T15:20:00+09:00"
related_paths:
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/benchmark/models.py"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "src/local_llm_benchmark/benchmark/runner.py"
  - "src/local_llm_benchmark/storage/base.py"
  - "src/local_llm_benchmark/storage/jsonl.py"
  - "tests/benchmark/test_runner.py"
  - "tests/storage/test_jsonl.py"
---

# 入力要件

- case-evaluations.jsonl と run-metrics.json の最小実装境界を設計したい。

# 整理した要件

- deterministic scorer のみを対象にし、既存の records.jsonl 保存と整合する形にする。
- acceptance として、少なくとも model_key x prompt_id 単位の集計を出せる必要がある。
- request_snapshot.evaluation.conditions は既に records.jsonl に保存されるため、新しい出力へ重複して持ち込む項目は最小化したい。
- 既存 ResultSink の責務境界は崩さず、manual または hybrid scorer と provider 依存情報は新ファイルへ混ぜない。

# 作業内容

- docs/architecture/benchmark-foundation.md、src/local_llm_benchmark/storage/jsonl.py、src/local_llm_benchmark/benchmark/models.py、src/local_llm_benchmark/benchmark/evaluation.py、tests/storage/test_jsonl.py、tests/benchmark/test_runner.py を確認し、現状の保存責務と request snapshot の保持項目を整理した。
- 既存の設計 task 00006-02 と evaluation-analyst の 00009-01 を照合し、ResultSink v1 が records/raw を正本としつつ、case-evaluations / run-metrics を拡張境界として予約している前提を再確認した。
- classification の macro_f1 のように run 集計時だけ label_space を使う metric があるため、scorer 実行と集計は storage ではなく benchmark 層で完結させる方が自然だと判断した。

# 判断

- deterministic scorer の実行責務は runner から呼ばれる benchmark 層の pure helper に置く。storage/jsonl.py は JSON 直列化とファイル管理に限定し、scorer 名や metric_definition を解釈しない。
- case-evaluations.jsonl は 1 case x 1 metric の lean な事実表にし、aggregation と threshold は run-metrics.json 側へ寄せる。これで request_snapshot.evaluation.conditions との二重管理を増やしすぎずに済む。
- run-metrics.json の最小集計 scope は model_key x prompt_id とし、prompt_category を scope に併記する。将来 case_id が prompt 内の複数サンプルへ広がっても scope を保ちやすい。
- BenchmarkRecord と request_snapshot の既存 schema は変更しない。benchmark/models.py への dataclass 追加も今回は見送り、case-evaluation / run-metric は dict payload のまま扱うのが最小変更である。
- ResultSink は同一 run_dir 配下の artifact writer として使い続け、write(record) に加えて評価 artifact を受け取る narrow method だけを増やすのが最小の protocol 変更である。
- record.error または response がない case は v1 では case-evaluations.jsonl へ行を出さず、records.jsonl を正本とする。run-metrics.sample_count は scored case 数を表す。

# 成果

## 推奨設計

- scorer 実行は BenchmarkRunner の責務配下に置き、実ロジックは src/local_llm_benchmark/benchmark/evaluation.py の pure helper へ寄せる。
- runner は各 case で次の順に進める。
  - BenchmarkRecord を作る。
  - records.jsonl 向けに sink.write(record) を呼ぶ。
  - response があり、かつ evaluation.conditions の evaluation_mode が auto の項目だけを deterministic scorer で評価する。
  - 1 case 分の case-evaluation 行群を sink へ渡す。
  - run 終了後に in-memory の case-evaluation 行群と条件定義を scope ごとに集計し、run-metrics.json を 1 回だけ書く。
- macro_f1 のように run 集計時だけ label_space が必要な metric は、runner 側の集計が request_snapshot.evaluation.conditions の metric_definition を参照して処理する。storage/jsonl.py に label_space 解釈を持たせない。
- ResultSink の最小拡張は次の 2 点で足りる。
  - write_case_evaluations(rows: list[dict[str, object]]) -> None
  - write_run_metrics(payload: dict[str, object]) -> None
- JsonlResultSink は case-evaluations.jsonl の append と run-metrics.json の最終書き込みを担当するが、scorer 実行や集計は担当しない。

## schema の最小項目

### case-evaluations.jsonl

- schema_version: case-evaluation.v1
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

補足:

- 1 行は 1 case x 1 metric を表す。
- score は case scorer の出力であり、macro_f1 行でも case 単位では exact_match_label の 0.0 または 1.0 を保持してよい。run 側の macro_f1 値は別途集計する。
- normalized_reference は reference_type が none の場合に null を許容する。
- details は open object とし、最小実装では scorer ごとに次のような失敗理由を入れられれば十分である。
  - extraction: missing_fields、mismatched_fields、parse_error
  - constraint_pass: failed_constraints
  - format_valid: format_errors
  - length_compliance: observed_length

### run-metrics.json

- schema_version: run-metrics.v1
- run_id
- metrics

metrics の各要素の最小項目:

- scope.model_key
- scope.prompt_id
- scope.prompt_category
- metric_name
- scorer_name
- scorer_version
- aggregation
- value
- threshold
- passed
- sample_count
- evaluation_mode

補足:

- 最小集計 scope は model_key x prompt_id で固定し、prompt_category を同時に残す。
- passed は threshold が null のとき null を許容し、threshold がある metric だけ true または false を入れる。
- sample_count は scored case 数であり、records.jsonl の record_count と同義ではない。
- run-metrics.json には deterministic かつ evaluation_mode = auto の metric だけを出す。

## 実装方針

- src/local_llm_benchmark/benchmark/models.py は今回は変更しない。既存の BenchmarkRecord と request_snapshot をそのまま使い、新しい評価出力は dict payload で運ぶ。
- src/local_llm_benchmark/benchmark/evaluation.py に、request snapshot builder と同居させる形で deterministic scorer helper と集計 helper を追加する。
- src/local_llm_benchmark/benchmark/runner.py は inference orchestration に加えて、評価 helper の呼び出しと、run 終了時の集計呼び出しを担う。
- src/local_llm_benchmark/storage/base.py は ResultSink protocol に評価 artifact 用の narrow method を足す。NoOp と MemoryResultSink も同じ面を実装し、テストしやすさを保つ。
- src/local_llm_benchmark/storage/jsonl.py は case-evaluations.jsonl の stream 管理と run-metrics.json の書き込みだけを追加し、scorer 名から挙動を分岐しない。
- artifact layout は安定させるため、scored case が 0 件でも run-metrics.json は空配列で生成し、case-evaluations.jsonl も空ファイルで残してよい。
- provider 依存情報は新ファイルへ追加しない。model_key、prompt_id、prompt_category、metric 名群までに留める。

## テスト観点

- benchmark/evaluation helper の unit test を追加し、classification、extraction、rewrite、summarization、short_qa、constrained_generation の deterministic scorer が期待どおりの score、passed、details を返すことを確認する。
- macro_f1 の集計 test を追加し、run 集計が case-evaluation の normalized_prediction / normalized_reference と conditions 内の label_space を使って model_key x prompt_id 単位に値を出せることを確認する。
- runner test では、1 case から conditions 数ぶんの case-evaluation 行が生成され、manual または hybrid metric が混ざらないことを確認する。
- storage/jsonl.py の test では、case-evaluations.jsonl と run-metrics.json が生成され、schema_version、scope、sample_count、provider 非依存性が守られることを確認する。
- error-path test では、adapter error の case が records.jsonl のみに残り、case-evaluations.jsonl に行を出さないか、少なくとも run-metrics の sample_count へ混入しないことを確認する。

# 次アクション

- programmer が benchmark 層の deterministic scorer helper、ResultSink の最小拡張、JsonlResultSink の artifact 追加、関連 unit test を実装する。
- reviewer が deterministic only の境界、provider 依存情報の不混入、sample_count と record_count の意味差が docs と実装で一致しているかを確認する。

# 関連パス

- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/benchmark/models.py
- src/local_llm_benchmark/benchmark/evaluation.py
- src/local_llm_benchmark/benchmark/runner.py
- src/local_llm_benchmark/storage/base.py
- src/local_llm_benchmark/storage/jsonl.py
- tests/benchmark/test_runner.py
- tests/storage/test_jsonl.py

# 設計対象

- deterministic scorer の実行責務を benchmark と storage のどちらへ置くか。
- case-evaluations.jsonl と run-metrics.json の最小 schema と、records.jsonl との重複境界。
- ResultSink を大きく壊さずに評価 artifact を追加する最小変更点。

# 設計判断

- scorer 実行と集計は benchmark 層、永続化は storage 層と分離する。
- case-evaluations.jsonl は lean な case 事実表、run-metrics.json は scope 付き集計表と役割を分ける。
- model_key x prompt_id を最小 scope とし、将来の multi-case 化に備えて sample_count と scope を分離する。
- 新しい dataclass は追加せず、既存の dict ベース snapshot と揃える。

# 影響範囲

- src/local_llm_benchmark/benchmark/evaluation.py の helper 追加。
- src/local_llm_benchmark/benchmark/runner.py の評価呼び出しと run 終了時集計。
- src/local_llm_benchmark/storage/base.py の protocol 追加。
- src/local_llm_benchmark/storage/jsonl.py と src/local_llm_benchmark/storage/stub.py の artifact writer 追加。
- tests/benchmark と tests/storage の unit test 拡張。

# リスク

- case-evaluations.jsonl だけでは macro_f1 の完全再集計に必要な label_space が足りない。v1 では records.jsonl の conditions と runner 内メモリを前提にする必要がある。
- 現状の case_id は model_key:prompt_id で固定されているため、sample_count は当面 1 になりやすい。この前提を scorer や集計へ埋め込むと後で広げにくい。
- adapter error を case-evaluations から外す設計のため、run-metrics.sample_count と manifest.record_count は一致しない場合がある。利用側へ意味差を明示する必要がある。

# 改善提案

- 後続で case-evaluations.jsonl 単体から offline 再集計したくなったら、aggregation と metric_definition の digest か label_space を case 行へ追加する。
- prompt 内の複数サンプル束縛を入れる段階では case_id だけを拡張し、run-metrics の scope は model_key x prompt_id のまま保つ。
- evaluation.py が肥大化したら scorer registry と aggregator だけを benchmark/scoring.py のような sibling module へ分離し、責務は benchmark 層に残す。