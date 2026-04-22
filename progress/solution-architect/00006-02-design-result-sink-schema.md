---
request_id: "00006"
task_id: "00006-02"
parent_task_id: "00006-00"
owner: "solution-architect"
title: "design-result-sink-schema"
status: "done"
depends_on:
  - "00006-01"
created_at: "2026-04-18T00:20:00+09:00"
updated_at: "2026-04-18T01:55:00+09:00"
related_paths:
  - "docs/architecture/benchmark-foundation.md"
  - "docs/architecture/prompt-and-config-design.md"
  - "src/local_llm_benchmark/benchmark/runner.py"
  - "src/local_llm_benchmark/storage"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/benchmark/models.py"
  - "prompts"
  - "tests"
---

# 入力要件

- ResultSink 実装前に、保存境界と保存スキーマを定義したい。
- raw response と正規化 record に加えて、評価条件の追跡に必要な情報も残したい。

# 整理した要件

- scorer 定義と閾値の結果を受けて、保存単位、ファイル構成、最小メタデータを整理する。
- 既存の BenchmarkRecord と責務境界を壊さない。

# 作業内容

- evaluation-analyst の scorer 定義、既存の BenchmarkRecord / ResultSink / stub 実装、runner、CLI、prompt metadata、README の方針を確認した。
- docs/architecture/benchmark-foundation.md に ResultSink v1 の保存境界、ディレクトリ構成、record schema、raw と normalized の分離方針、評価条件と評価結果の境界、CLI と runner の注入点を追記した。
- BenchmarkRecord を壊さずに request_snapshot を拡張する案を採用し、programmer が更新すべきファイルと実装順を具体化した。

# 判断

- ResultSink は保存専任に留め、prompt や scorer 定義の再解釈は runner 側で済ませてから record を渡す。
- 初期保存形式は tmp/results/<run_id>/ 配下の JSONL + raw JSON 分離が最も現実的。JSONL を正本にすると case 単位 append が簡単で、raw payload の肥大化も避けやすい。
- BenchmarkRecord の dataclass は変更せず、request_snapshot に prompt_snapshot と evaluation をネストして保存情報を追加する。これが最小変更で実装しやすい。
- expected_output_format と output_contract_snapshot は metric ごとではなく evaluation 共通コンテキストへ 1 回だけ置く。metric 固有なのは scorer と aggregation と threshold 系のみとする。
- 評価結果は inference 保存と分離し、case-evaluations.jsonl と run-metrics.json を将来の scorer 境界として予約する。request 00006 の初期実装では conditions 保存までを必須とし、evaluation result ファイルは optional 扱いにする。
- provider 依存情報は provider_id と provider_model_name と raw response に限定し、provider profile の connection や自動ダウンロード前提は保存しない。

# 成果

## 保存ディレクトリ構成

```text
tmp/
  results/
    <run_id>/
      manifest.json
      records.jsonl
      raw/
        00001-<safe-case-key>.json
      case-evaluations.jsonl
      run-metrics.json
```

- manifest.json は run 単位の plan スナップショットと保存件数を持つ。
- records.jsonl は正規化済み record の正本。
- raw/ は provider payload を case ごとに分離保存する。
- case-evaluations.jsonl と run-metrics.json は scorer 実装後の拡張境界で、初期実装では未作成でもよい。

## 1 record あたりの保存項目

- schema_version: benchmark-record.v1
- run_id, case_id, model_key, prompt_id
- request_snapshot.suite_id
- request_snapshot.provider_id
- request_snapshot.provider_model_name
- request_snapshot.generation
- request_snapshot.prompt_bindings
- request_snapshot.trace_metadata
- request_snapshot.prompt_snapshot.version
- request_snapshot.prompt_snapshot.category
- request_snapshot.prompt_snapshot.tags
- request_snapshot.prompt_snapshot.evaluation_metadata_snapshot
- request_snapshot.evaluation.expected_output_format
- request_snapshot.evaluation.output_contract_snapshot
- request_snapshot.evaluation.reference_snapshot
- request_snapshot.evaluation.conditions
- response.output_text
- response.usage
- response.latency_ms
- response.finish_reason
- response.provider_metadata
- response.raw_response_path
- error

request_snapshot.evaluation.conditions の各要素には次を持たせる。

- metric_name
- scorer_name
- scorer_version
- reference_type
- aggregation
- threshold
- pass_rule
- metric_definition
- evaluation_mode

threshold は null または object とし、初期形は null、{"type": "min", "value": 1.0}、{"type": "range", "min": 80, "max": 120, "unit": "chars"} を許容する。

## raw と normalized の分離方針

- records.jsonl は比較と再集計に必要な provider 非依存情報の正本にする。
- raw response は別ファイルに逃がし、records 側は raw_response_path だけを保持する。
- raw ファイルには run_id、case_id、provider_id、provider_model_name を添えて自己記述的にする。
- provider profile の connection、settings、認証、モデル取得状態は保存対象に含めない。

## 評価条件と評価結果の持ち方

- 評価条件は request_snapshot.evaluation に保存し、prompt metadata の生値と、run 時点で解決した scorer 条件を分ける。
- prompt の evaluation_metadata は provenance として request_snapshot.prompt_snapshot.evaluation_metadata_snapshot に残す。
- expected_output_format と output_contract_snapshot は evaluation 共通コンテキストに置く。
- case ごとの正解値が必要な場合は PromptSpec.metadata.evaluation_reference から reference_snapshot へ凍結する。classification では label、extraction では expected_fields、short_qa では expected_text を想定する。
- case 評価結果は case-evaluations.jsonl に分け、score、passed、normalized_prediction、normalized_reference、details を 1 case 1 metric 単位で保存する。
- run 集計結果は run-metrics.json に分け、scope ごとに metric_name、aggregation、value、threshold、passed、sample_count を持たせる。

## CLI や runner からの注入点

- src/local_llm_benchmark/cli/main.py
  - build_benchmark_plan の直後で output_root を決め、JsonlResultSink(output_root, plan) を構築する。
  - 既定出力先は tmp/results とし、run_id ごとのサブディレクトリを sink 側で作る。
- src/local_llm_benchmark/benchmark/runner.py
  - request_snapshot を組み立てる箇所で prompt_snapshot と evaluation を追加する。
  - evaluation.conditions は runner 側の resolver で固定し、sink には完成した snapshot だけを渡す。
  - response.raw_response は sink が別ファイルへ出し、records 側は raw_response_path へ置き換える。
- src/local_llm_benchmark/storage
  - ResultSink Protocol は維持し、JSONL 実装で manifest 初期化と close 時の件数確定を行う。

## programmer が更新すべきファイルの指示

- src/local_llm_benchmark/benchmark/runner.py
  - request_snapshot に prompt_snapshot と evaluation を追加する helper を実装する。
- src/local_llm_benchmark/storage/base.py
  - Protocol は原則維持し、必要なら constructor 想定を docstring で補足する。
- src/local_llm_benchmark/storage/stub.py
  - MemoryResultSink は既存テスト互換を維持する。NoOp は fallback として残す。
- src/local_llm_benchmark/storage/jsonl.py
  - JsonlResultSink を新設し、manifest、records.jsonl、raw/ を管理する。
- src/local_llm_benchmark/cli/main.py
  - JsonlResultSink を既定で注入できるようにし、必要なら output dir を受け取る option を追加する。
- prompts/classification/contact-routing-v1.toml
  - manual_review ではなく deterministic metric を表す evaluation_metadata と metadata.evaluation_reference を入れる。
- prompts/extraction/invoice-fields-v1.toml
  - exact_match_json_fields と json_valid の前提になる output_contract と metadata.evaluation_reference を入れる。
- prompts/rewrite/polite-rewrite-v1.toml
  - constraint_pass の前提になる machine-readable な output_contract を入れる。
- tests/benchmark/test_runner.py
  - request_snapshot に evaluation 情報が乗ることを確認する。
- tests
  - storage 用テストを追加し、records と raw の分離、manifest の件数確定、error record の保存を確認する。

# 次アクション

- programmer が JSONL ResultSink、runner の snapshot 拡張、prompt metadata 更新、CLI 注入、関連テストを実装する。
- reviewer が docs と実装と prompt metadata の整合、および provider 依存情報の最小化を確認する。

# 関連パス

- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/storage
- src/local_llm_benchmark/benchmark/models.py

# 設計対象

- ResultSink が保持すべき保存単位と、inference 保存と評価保存の責務境界。
- BenchmarkRecord を壊さずに実装できる record schema と request_snapshot の拡張点。
- CLI と runner のどこで保存先と評価条件を確定するか。

# 設計判断

- inference 時点の正本は records.jsonl と raw/ の 2 系統に分ける。
- metric ごとの scorer 条件は request_snapshot.evaluation.conditions に凍結し、sink はそれを書くだけにする。
- expected_output_format と output_contract_snapshot は共通コンテキストへ寄せ、metric ごとの重複を避ける。
- case ごとの正解値は PromptSpec.metadata.evaluation_reference から reference_snapshot へ凍結する方針とし、新 dataclass 追加は見送る。
- 評価結果の保存ファイルは schema だけ先に決め、request 00006 の初期実装では optional に留める。

# 影響範囲

- src/local_llm_benchmark/benchmark/runner.py の request_snapshot 組み立て。
- src/local_llm_benchmark/storage 配下の具体実装追加と serializer。
- src/local_llm_benchmark/cli/main.py の ResultSink 注入。
- prompts 配下の evaluation_metadata、output_contract、metadata.evaluation_reference。
- tests の runner と storage まわり。

# リスク

- prompt 側に machine-readable な reference_snapshot が入らないまま scorer だけ実装すると、accuracy や exact_match_rate の再計算ができない。
- raw response を case_id そのままのファイル名で保存すると、記号や衝突で壊れやすい。
- manual 評価の prompt が残った状態で自動評価条件を推測すると、docs と保存内容がずれる。

# 改善提案

- evaluation.conditions を組み立てる resolver は storage 直下ではなく再利用しやすい専用モジュールへ切り出す。
- run-metrics.json は将来 model_key と prompt_id を scope に含め、run 全体集計だけに閉じない形へしておく。
- README では provider ごとのモデル取得を自動化しない方針を短く明記し、保存物には provider connection 情報を含めないと揃える。