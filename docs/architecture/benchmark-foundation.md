# ベンチマーク基盤アーキテクチャ

## 目的

- Ollama を最初の provider 実装として採用しつつ、benchmark core は provider 非依存で保つ。
- config、model registry、prompt 管理、保存処理を分離し、Python 実装担当が最小スキャフォールドを段階的に組める状態にする。
- request 00006 では、ResultSink v1 の保存境界と JSON 系の初期保存スキーマまで固定する。

## 設計対象

- provider 非依存の benchmark core
- provider adapter と provider client
- config 管理
- model registry
- prompt 管理
- 結果保存境界と初期保存スキーマ

## 責務境界

| コンポーネント | 主責務 | 今回は含めないもの |
| --- | --- | --- |
| benchmark core | 実行計画の反復、Prompt と Model の組み合わせ解決、provider 呼び出し、正規化済み実行記録の組み立て | HTTP 通信、provider 固有 payload、永続化方式の詳細 |
| provider adapter | 共通の InferenceRequest を provider 固有 request に変換し、provider client を使って応答を共通形へ戻す | 設定ファイル読み込み、prompt 保管、実行結果の保存 |
| provider client | 実際の API 呼び出し、タイムアウト、接続エラー変換、raw response の取得 | benchmark の反復制御、モデル選定、評価指標の計算 |
| config 管理 | 実行設定、provider 接続設定、既定 generation 設定、利用 registry の参照先を読み込んで検証する | 実リクエスト送信、prompt 本文の編集 UI |
| model registry | provider をまたいだモデル識別子の正規化、capability や既定パラメータの保持、benchmark plan からのモデル解決 | provider API の直接呼び出し |
| prompt 管理 | prompt 定義の保管、カテゴリ付与、system/user message とメタデータの取得 | provider ごとの payload 生成 |
| 保存処理 | 実行結果を受け取る抽象境界を提供し、ResultSink v1 では raw payload と normalized record を JSON 系ファイルへ分離保存する | scorer 実装そのもの、集計レポート UI |

## 推奨ディレクトリ構成

```text
src/local_llm_benchmark/
  benchmark/
    models.py
    protocols.py
    runner.py
  config/
    models.py
    loader.py
  registry/
    models.py
    model_registry.py
  prompts/
    models.py
    repository.py
  providers/
    base.py
    ollama/
      adapter.py
      client.py
    openai_compatible/
      adapter.py
      client.py
  storage/
    base.py
    stub.py
  cli/
    main.py

tests/
  benchmark/
  providers/
  registry/
  prompts/
  storage/
```

- benchmark は実行オーケストレーションだけを持ち、provider 名を知らない。
- providers/base.py は provider 実装の共通 Protocol と例外だけを置く。
- providers/ollama は最初の具体実装であり、ほか provider の追加時は同じ階層へ並列追加する。
- providers/openai_compatible は OpenAI-compatible local server 向けの実装で、v1 は non-streaming の `/chat/completions` だけを扱う。
- registry と prompts は初期段階では静的ファイルや in-memory 実装でもよいが、呼び出し側には抽象を見せる。
- storage は stub から着手してよいが、request 00006 では JSONL 実装を既定の保存方式として扱う。集計やレポートは別段階へ送る。
- storage の初期実装は JSONL を正本にし、raw response と評価条件スナップショットを分離保存する。

## 主要 dataclass と Protocol

### dataclass

- BenchmarkPlan
  - run_id、provider_profiles、model_keys、prompt_ids、default_generation を保持する実行単位。
- GenerationSettings
  - temperature、top_p、max_tokens、seed など再現性に関わる値を保持する。
- ModelSpec
  - model_key、provider_id、provider_model_name、capabilities、default_generation を保持する正規化済みモデル定義。
- PromptSpec
  - prompt_id、category、system_message、user_message、metadata、parameter_overrides を保持する。
- InferenceRequest
  - model、prompt、generation、trace_metadata を束ねて adapter へ渡す共通 request。
- InferenceResponse
  - output_text、raw_response、usage、latency_ms、finish_reason、provider_metadata を共通形で返す。
- BenchmarkRecord
  - run_id、case_id、model_key、prompt_id、request_snapshot、response、error を持つ保存用の最小単位。

### Protocol

- ProviderAdapter
  - infer(request: InferenceRequest) -> InferenceResponse
  - adapter 名は provider_id と 1 対 1 を基本とし、core はこの Protocol だけに依存する。
- ModelRegistry
  - get(model_key: str) -> ModelSpec
  - list(provider_id: str | None = None) -> list[ModelSpec]
- PromptRepository
  - get(prompt_id: str) -> PromptSpec
  - list(category: str | None = None) -> list[PromptSpec]
- ResultSink
  - write(record: BenchmarkRecord) -> None
  - close() -> None
  - 実装は constructor で run 単位の情報を受け取り、manifest と records.jsonl、raw response を管理する。

## 依存方向

依存は次の一方向にそろえる。

1. cli/main.py が config を読み、runner に依存オブジェクトを注入する。
2. benchmark/runner.py は BenchmarkPlan、ModelRegistry、PromptRepository、ProviderAdapter、ResultSink にだけ依存する。
3. providers/ollama/adapter.py は providers/ollama/client.py に依存し、Ollama 固有の request 変換を閉じ込める。
4. storage/stub.py は ResultSink を実装するが、runner は具体保存方式を知らない。
5. config/loader.py は設定ファイルを dataclass 群へ変換するが、provider API や secret は読まない。

core から見える依存のイメージは次の通り。

```text
CLI / bootstrap
  -> ConfigLoader
  -> BenchmarkRunner
       -> ModelRegistry
       -> PromptRepository
       -> ProviderAdapter
       -> ResultSink

OllamaAdapter
  -> OllamaClient
```

## Secret と readiness

- config loader は provider profile の `connection` を generic mapping として読むだけで、API キー値や環境変数は解決しない。
- secret 解決は provider factory の明示契約だけを扱う。`openai_compatible` では `connection.api_key_env` を使い、未指定なら Authorization header なしで接続する。指定済みなのに参照先環境変数が未設定または空文字なら、factory で configuration error にする。平文 `connection.api_key` は受け付けない。
- readiness は 2 段に分ける。code readiness は `suites --config-root configs` で config と CLI の結線を確認する段階、environment readiness は local server 起動、必要な model identifier 準備、必要なら環境変数 export の後に `run --config-root configs --suite ...` を通す段階とする。
- OpenAI-compatible local server の readiness では、server 起動と model alias load を別手順として扱う。LM Studio の `lms server start` は server を立ち上げるだけで、`lms load <model_key> --identifier llmb-minimal-chat` のような明示 load を置き換えない。
- LM Studio では `lms ls` に出る actual downloaded model key を provider model identifier の基準に読む。repo 同梱の `llmb-minimal-chat` は readiness alias slot であり、一貫性を優先する run では actual key を使う別 model entry に寄せる。
- `openai-compatible-minimal-v1` は OpenAI-compatible readiness 用の 1 model x 3 prompts 最小 suite とし、既定の Ollama baseline と正式比較用の suite とは分けて扱う。

## Cross-provider loading policy

- runner は逐次実行で、model と prompt の組み合わせを 1 件ずつ処理する。
- benchmark core は provider 非依存を保ち、model の download、load、pin、unload を自動化しない。
- 実際の residency と eviction は provider 運用へ委ねる。Ollama は request ごとの `keep_alive`、LM Studio の OpenAI-compatible 経路は server 側の JIT loading、Idle TTL、Auto-Evict の既定動作で読む。

## 初期 provider の位置づけ

- Ollama は最初の provider 実装であり、基盤全体の標準 API ではない。
- benchmark core が知るのは ProviderAdapter と共通 dataclass だけに留める。
- Ollama 固有の base_url、model pull 前提、chat または generate の差分は providers/ollama 配下へ閉じ込める。
- request 00010 では `openai_compatible` provider を追加し、v1 は non-streaming の `/chat/completions` だけを扱う。
- LM Studio、vLLM、llama.cpp server 系は、`openai_compatible` profile の base_url と model alias 差し替えで扱う方針とする。
- 将来 LM Studio、vLLM、llama.cpp server などを追加するときは、同じ Protocol を実装する adapter/client ペアを追加するだけでよい構造を目指す。

## 初期実装の優先順位

1. 共通 dataclass と Protocol を先に固定する。
2. config loader と静的な model registry、prompt repository を実装する。
3. OllamaAdapter と OllamaClient を追加し、単一 request の疎通を確認する。
4. BenchmarkRunner で model と prompt の直積または明示ケースを反復できるようにする。
5. JSONL ベースの ResultSink をつなぎ、raw response と評価条件スナップショットを含む実行記録を保存できる状態にする。

## request 00006: ResultSink 保存スキーマ v1

初期実装では tmp/results/<run_id>/ を既定の出力先とし、records.jsonl を正規化済み record の正本、raw/ を provider payload の退避先として扱う。tmp/ は既に ignore 対象であり、試行錯誤の保存先として扱いやすい。

### 保存ディレクトリ構成

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

- manifest.json は run 単位のメタデータ、plan の最小スナップショット、保存レイアウト、最終件数を持つ。
- records.jsonl は 1 case 1 line の正規化済み実行 record を持つ。
- raw/ は provider payload を case ごとに分離し、records.jsonl から raw_response_path で参照する。
- case-evaluations.jsonl と run-metrics.json は request 00009 の最小スライスで実装し、records.jsonl と同じ run_dir 配下へ保存する。

### 1 record あたりの保存項目

records.jsonl の 1 行は、BenchmarkRecord を崩さずに直列化した JSON とし、少なくとも次を持つ。

| 項目 | 役割 |
| --- | --- |
| schema_version | record スキーマの版。初期値は benchmark-record.v1 とする |
| run_id, case_id, model_key, prompt_id | 既存 BenchmarkRecord の識別子をそのまま残す |
| request_snapshot | suite_id、provider_id、provider_model_name、generation、prompt_bindings、trace_metadata を持つ request スナップショット |
| request_snapshot.prompt_snapshot | prompt_version、prompt_category、tags、evaluation_metadata_snapshot を持つ prompt 側の凍結情報 |
| request_snapshot.evaluation | expected_output_format、output_contract_snapshot、reference_snapshot、conditions を持つ評価コンテキスト |
| response | output_text、usage、latency_ms、finish_reason、raw_response_path を持つ正規化済み応答 |
| error | 実行失敗時のエラー文字列。成功時は null |

raw_response 自体は records.jsonl に埋め込まず、raw/ 配下の JSON ファイルへ逃がす。response.raw_response_path だけを records.jsonl 側へ残す。

### raw と normalized の分離方針

- normalized 側には provider 非依存で比較や再集計に必要な値だけを残す。具体的には output_text、usage、latency_ms、finish_reason、model_key、prompt_id、評価条件スナップショットを正本にする。
- raw 側には provider 固有の payload をそのまま保存し、必要なら provider_id、provider_model_name、run_id、case_id、provider_metadata を添えて自己記述的な JSON にする。
- provider profile の connection、settings、モデル自動取得状態のような provider 運用情報は保存しない。records 側で持つ provider 依存情報は provider_id と provider_model_name までに留める。

### 評価条件と評価結果の持ち方

評価条件は request_snapshot.evaluation.conditions に metric ごとの配列で保存する。metric ごとに次の項目を持つ。

- metric_name
- scorer_name
- scorer_version
- reference_type
- aggregation
- threshold
- pass_rule
- metric_definition
- evaluation_mode

expected_output_format と output_contract_snapshot は metric ごとではなく request_snapshot.evaluation の共通コンテキストとして 1 回だけ持つ。どの metric でも同じ prompt 出力契約を参照するためである。

threshold は null または object とし、初期実装では次の形を許容する。

- null: 閾値未固定または情報表示のみ
- {"type": "min", "value": 1.0}: 下限閾値
- {"type": "range", "min": 80, "max": 120, "unit": "chars"}: 範囲閾値

metric_definition は scorer の解釈条件を入れる自由度の高い mapping とし、分類では prediction_path、label_space、normalization、抽出では required_fields、長さ系では length_unit と min_chars/max_chars、制約系では constraint_ids を持たせる。

評価結果は inference record と分離し、後続の scorer 実装で次の 2 境界に書く。

- case-evaluations.jsonl: run_id、case_id、metric_name、scorer_name、scorer_version、score、passed、normalized_prediction、normalized_reference、details を 1 case 1 metric 単位で保存する。
- run-metrics.json: scope として run_id を必須にし、必要に応じて model_key、prompt_id、prompt_category を持つ集計結果を配列で保存する。各要素は metric_name、aggregation、value、threshold、passed、sample_count を持つ。

## request 00009: deterministic evaluation 出力

- scorer 実行と run 集計は benchmark 層で行い、storage は case-evaluations.jsonl と run-metrics.json の書き出しだけを担当する。
- case-evaluations.jsonl は 1 case x 1 metric を正本とし、normalized_prediction、normalized_reference、details を保持する。
- run-metrics.json の最小 scope は model_key x prompt_id で、prompt_category を併記する。
- adapter error など response を持たない record は records.jsonl には残すが、case-evaluations と run-metrics の sample_count には含めない。
- extraction と constrained_generation では、strict row の `exact_match_rate`、`json_valid_rate`、`constraint_pass_rate`、`format_valid_rate` に加え、前後空白除去とレスポンス全体が単一 fenced block のときだけ wrapper を外す payload row の `json_payload_valid_rate`、`payload_exact_match_rate`、`payload_format_valid_rate`、`payload_constraint_pass_rate` を別 metric 名で保存する。payload row は diagnostic であり、strict fail を上書きしない。

### CLI と runner の注入点

- CLI は build_benchmark_plan の直後で ResultSink 実装を組み立てる。初期実装では JsonlResultSink(output_root, plan) のように plan を constructor へ渡し、manifest.json と保存先ディレクトリを sink 側で初期化する。
- 既定の output_root は tmp/results とし、必要なら CLI option で差し替える。
- BenchmarkRunner は ResultSink に prompt repository を再注入しない。runner が prompt と model を解決できる時点で request_snapshot を組み立て、prompt_snapshot と evaluation を埋めてから BenchmarkRecord を生成する。
- ResultSink は保存専任とし、scorer の解決や prompt 定義の再解釈は行わない。scorer 定義の固定値は runner から受け取った evaluation.conditions をそのまま書く。

### 実装時の最小変更方針

- BenchmarkRecord の dataclass は変更しない。request_snapshot の内容を拡張し、serializer が JSON へ落とす。
- ResultSink Protocol の write(record) / close() は維持し、run 開始処理は具体実装の constructor で吸収する。
- prompt ごとの machine-readable な参照値は新しい dataclass を増やさず、当面は PromptSpec.metadata の evaluation_reference から取り出して request_snapshot.evaluation.reference_snapshot へ凍結する。

## request 00011: single-run report CLI

- `local-llm-benchmark report --run-dir <run_dir>` を、保存済み single-run の `manifest.json` と `run-metrics.json` をまとめて読む stable 入口とする。
- 既定表示の最小列は header の `run_id`、`suite_id`、`run_dir`、`records`、`metric_rows` と、row の `scope=model_key | prompt_category | prompt_id`、`metric_name`、`value`、`threshold`、`passed`、`n` とする。
- `value` は固定小数 3 桁、`threshold` は `null -> -`、`min -> >=1.0`、`range -> 80-120 chars` のように整形する。run gate を評価しない row は `passed=n/a` とする。
- `records` は manifest の `record_count`、`n` は run-metrics の `sample_count` であり同義ではない。`record_count` は保存された run 全体の record 数、`sample_count` はその metric を計算できた case 数で、実行失敗または `evaluation_mode != auto` の record は含まない。
- 比較レポート本体では、この row 正規化を再利用しつつ multi-run 比較へ広げる。

## request 00015: multi-run compare CLI

- `local-llm-benchmark compare --run-dir <run_a> --run-dir <run_b> [...]` を、保存済み multi-run の stable 比較入口とする。先頭の `--run-dir` を baseline とし、入力順を保持する。
- compare は `load_run_report()` を再利用し、row key を `model_key | prompt_category | prompt_id | metric_name` に固定する。storage schema や provider 実装は変えない。
- 既定表示は differing rows のみとし、identical rows は header の `identical_rows_omitted` 件数へ逃がす。差分判定には `value`、`passed`、`sample_count`、`threshold` 表示、row presence を含める。
- row が存在しない場合は `missing` と表示する。これは run error、`evaluation_mode != auto`、suite / plan 差分などで該当 metric row が存在しないことを表す。
- `threshold` は全 run で同一なら 1 回だけ表示し、異なる場合は `threshold=varies` とする。閾値差分は error ではなく可視化対象として扱う。
- compare の legend / note では、`json_valid_rate` と `format_valid_rate` は raw JSON-only contract を見る strict gate、`constraint_pass_rate` は exact lexical / structural contract を見る strict gate、`json_payload_valid_rate`、`payload_exact_match_rate`、`payload_format_valid_rate`、`payload_constraint_pass_rate` は前後空白除去と単一 fenced block unwrap だけを許す payload diagnostic であり strict fail を上書きしないことを明示する。semantic quality や自然な rewrite 品質は別論点として扱う。
- `suite_id` 不一致は hard error にせず header note として表示する。比較の正本は row key であり、suite 差分は provenance として補足する。

## リスク

- model registry と config の責務を曖昧にすると、同じモデル情報が設定ファイルと provider 実装へ重複する。
- provider adapter に retry、正規化、保存判断まで詰め込むと、将来 provider 追加時に差分が大きくなる。
- prompt 側で provider 固有オプションを直接持ち始めると、比較データとしての再利用性が下がる。

## 改善提案

- provider ごとの capability を boolean 群ではなく feature 名の集合で持つと、将来の chat/completion/embedding 拡張に耐えやすい。
- 実装初期から raw response と正規化レスポンスを分離しておくと、後続の評価指標追加で保存仕様を崩しにくい。
- ResultSink は同期 API から始めてよいが、runner 側はバッチ保存へ差し替えられるよう 1 箇所注入に留めると拡張しやすい。