# Prompt と Config 設計メモ

## 目的

- provider 実装から独立した prompt corpus を定義し、同じ prompt を複数のローカル LLM 実行基盤で再利用できるようにする。
- benchmark suite、model selection、prompt set の関係を明確にし、設定だけで比較条件を差し替えやすくする。
- Python 側で dataclass に落とし込みやすい最小レコードを先に固め、後続実装の責務分割を簡単にする。

## 基本方針

- prompt template には provider 名、API パス、tokenizer 前提のような実行基盤依存情報を持ち込まない。
- prompt corpus は system_message、user_message、variables、評価メタデータを持つ比較用データとして扱う。
- model ごとの差分は model registry へ寄せ、prompt 側は task 要件と期待出力の表現に集中させる。
- benchmark suite は model selection と prompt set を束ねる上位設定とし、公平性を保つための generation parameter 上書きもここで扱う。

## 小型モデル比較向けの初期カテゴリ案

| category | 用途 | 小型モデル向けの理由 | 主な評価軸 |
| --- | --- | --- | --- |
| classification | 単一ラベルまたは少数ラベルの分類 | 出力が短く、比較が安定しやすい | accuracy, macro_f1 |
| extraction | 短文からの項目抽出、JSON 化 | 入力と正解の対応が明確 | exact_match, json_valid_rate |
| rewrite | 口調変更、要約前の整形、言い換え | 生成長が短く、差分比較しやすい | constraint_pass_rate, similarity |
| summarization | 短めの本文の要約 | 長文耐性に依存しすぎず導入しやすい | rouge_like, length_compliance |
| short_qa | 短い文脈または基本知識への回答 | 推論負荷を抑えて比較できる | exact_match, factuality_check |
| constrained_generation | 箇条書き数、文字数、必須語句、JSON などの制約付き生成 | instruction follow の差が見えやすい | constraint_pass_rate, format_valid_rate |

初期セットでは、長大コンテキスト、ツール呼び出し、複数段の外部参照、長いコード生成は外す方がよい。小型モデル比較の初期段階では、短い入力、単一ターン、出力制約が明確な prompt を優先する。

この表は候補指標も含む。現行実装で公式 auto 評価に採用しているのは、後述の deterministic scorer とその run 集計だけであり、similarity、rouge_like、factuality_check はまだ採用していない。

## 推奨レコード構造

### 1. prompt category

- task の大分類。集計と prompt set フィルタに使う。
- 例: classification, extraction, rewrite, summarization, short_qa, constrained_generation

### 2. prompt template record

最低限の推奨項目は次のとおり。

| 項目 | 役割 |
| --- | --- |
| prompt_id | 一意識別子。バージョン込みで運用しやすい名前にする |
| version | 互換性確認用。prompt 改訂を追跡する |
| category | 集計用のカテゴリ |
| title | 人が識別しやすい短い名称 |
| description | 目的と比較観点を 1 文で示す |
| system_message | モデルへの恒常的な役割指示 |
| user_message | 実データ埋め込み前のテンプレート本文 |
| variables | 差し込み変数の定義 |
| recommended_generation_parameters | task に適した推奨生成条件 |
| tags | prompt set や検索のための補助タグ |
| evaluation_metadata | 正解形式、評価指標、難度など |
| output_contract | 任意。期待形式を明示したい場合に追加 |

variables の推奨項目は name、type、required、description、default、example、validation とする。テンプレート展開記法は {{variable_name}} のような単純置換を前提にすると実装を選びにくい。

recommended_generation_parameters には temperature、top_p、max_output_tokens、stop、seed を置けるようにする。すべて必須にはせず、未指定時は model registry または suite 側の値を使う。

evaluation_metadata の最低限の推奨項目は primary_metric、secondary_metrics、reference_type、scorer、difficulty、language、expected_output_format とする。
reference_type は primary_metric の参照型として扱い、secondary_metrics が別の参照型や pass 条件を使う場合は ResultSink 側の metric_definition で追跡する。

### 3. tags

タグはカテゴリの代替ではなく、横断的な絞り込みに使う。

- 例: ja, short-context, small-model-friendly, deterministic, json-output, baseline, customer-support

## request 00006: 初期 scorer 定義と閾値

評価では scorer と集計 metric を分けて扱う。

- scorer は 1 case 単位で normalized prediction と reference を比較し、boolean または scalar を返す。
- metric は scorer 出力を run 単位で集計した値で、accuracy や macro_f1 のような比較指標になる。
- prompt の evaluation_metadata.scorer は primary_metric を支える主 scorer 名とし、scorer_version と metric_definition は ResultSink が実行時に固定値として保存する。
- README で exact_match と書く項目は、保存と集計では case scorer と run metric に分け、run 側では exact_match_rate のような名前で扱う。

### 初期フェーズで固定する deterministic scorer

| scorer_name | scorer_version | 主なカテゴリ | reference_type | 判定内容 | case pass 条件 |
| --- | --- | --- | --- | --- | --- |
| exact_match_label | v1 | classification | label | JSON または text からラベルを取り出し、NFKC と前後空白除去の後に正解ラベルと一致するかを見る | normalized prediction と reference が一致 |
| exact_match_text | v1 | short_qa | text | 短い正答文を NFKC と前後空白除去の後に比較する | normalized prediction と reference が一致 |
| exact_match_json_fields | v1 | extraction | json | JSON を parse し、required_fields の値を field ごとに比較する | JSON が parse でき、required_fields がすべて一致 |
| json_valid | v1 | extraction | none | JSON として parse できるかを見る | parse 成功 |
| format_valid | v1 | constrained_generation | none | expected_output_format と output_contract に合う構造かを見る | 構造検証に成功 |
| constraint_pass | v1 | rewrite, constrained_generation | none | output_contract の明示制約をすべて満たすかを見る | failed_constraints が 0 |
| length_compliance | v1 | summarization | none | output_contract の文字数レンジに収まるかを見る | min_chars 以上かつ max_chars 以下 |

v1 の exact_match 系は過剰な吸収を避け、正規化は最小限に留める。文字列は NFKC と前後空白除去、数値は数値型比較、日付は reference 側を ISO-8601 に正規化しておく前提とする。

現行実装で constraint_pass v1 が見るのは required_phrases、forbidden_phrases、sentence_count、required_values である。format_valid v1 は expected_output_format と output_contract に基づいて、json_object の required_keys / allowed_keys / field_types、bullet_list、text の基本構造だけを検証する。length_range は length_compliance v1 が別に扱う。語調の自然さ、意味保持、regex、箇条書き数、自由文の類似度は v1 の自動 pass 判定に含めない。

### カテゴリ別の初期固定方針

| category | 初期フェーズで固定する自動評価 | 主な集計 metric | 固定した pass 条件 | まだ固定しない項目 |
| --- | --- | --- | --- | --- |
| classification | exact_match_label v1 | accuracy, macro_f1 | case pass は exact_match = 1。run の絶対閾値は dataset 較正前なので未固定 | なし |
| extraction | exact_match_json_fields v1, json_valid v1 | exact_match_rate, json_valid_rate | case pass は json_valid = 1 かつ exact_match = 1。運用 gate として json_valid_rate = 1.0 は固定してよい | field ごとの重み付け、部分点 |
| rewrite | constraint_pass v1 のみ | constraint_pass_rate | output_contract に machine-readable 制約がある場合だけ自動 pass/fail を使う | similarity は v0 または manual。意味保持と自然さは manual または hybrid |
| summarization | length_compliance v1 のみ | length_compliance_rate | min_chars と max_chars の範囲内なら pass | rouge_like は v0 または manual |
| short_qa | exact_match_text v1 のみ | exact_match_rate | case pass は exact_match = 1 | factuality_check は manual または hybrid |
| constrained_generation | constraint_pass v1, format_valid v1 | constraint_pass_rate, format_valid_rate | required constraints と format がともに満たされる | semantic quality score は後続 |

rewrite と summarization は、README にある候補指標のうち deterministic な部分だけを v1 で固定し、類似度や要約妥当性のような較正不足の指標は公式 pass/fail に使わない。

### 初期フェーズで固定しない scorer

| scorer 候補 | 状態 | 固定しない理由 | 暫定方針 |
| --- | --- | --- | --- |
| similarity | v0 または manual | 日本語の言い換えで lexical overlap と意味保持がずれやすく、embedding や judge 依存も大きい | manual review の補助指標に留め、pass/fail には使わない |
| rouge_like | v0 または manual | 日本語 tokenization、複数参照要約、要点抽出の較正が未完了 | 実験的集計に留め、正式比較から外す |
| factuality_check | manual または hybrid | 根拠データ、判定ルーブリック、judge の責務分離が未定 | short_qa は当面 exact_match 中心、事実性は manual review |

## request 00012: 現行評価とランダム性の整理

- 現行の evaluation.conditions は prompt.category から固定解決し、公式 auto 評価として出力する scorer は exact_match_label、exact_match_text、exact_match_json_fields、json_valid、constraint_pass、length_compliance、format_valid の 7 つだけである。
- case-evaluations.jsonl と run-metrics.json に流すのは、response があり、かつ evaluation_mode = auto の条件だけである。manual / hybrid と unsupported scorer は現行の公式比較に含めない。
- レーベンシュタイン距離、文字列類似度、ROUGE-like、embedding 類似度、LLM judge は未採用であり、現行の公式 auto 評価には含めない。
- json_valid_rate は JSON parse 成功だけを見る。required_fields の一致は exact_match_rate、JSON object の key や型の妥当性は format_valid_rate で別に追う。
- 現行の run gate は json_valid_rate >= 1.0 と format_valid_rate >= 1.0 だけで、length_compliance_rate を含む他の metric は比較用の観測値として扱う。
- ランダム性への対応は generation snapshot の保存と低温度設定に留まる。sample baseline suite は temperature 0.0、top_p 0.95、seed 7 を上書きするが、seed の適用は provider 依存である。Ollama は seed を送る一方、OpenAI-compatible v1 は送らない。
- したがって現行方式で確認しやすいのは、単一正解や機械可読制約を持つ task の完走性、形式妥当性、制約遵守である。意味保持、要約品質、言い換え許容、run 間分散は未対応である。

### ResultSink が追跡する評価条件

ResultSink では、prompt の evaluation_metadata だけでなく、実行時に解決された evaluation_conditions を metric ごとに保存した方がよい。secondary metric が primary と異なる reference_type や pass 条件を使うためである。

| 保存項目 | 粒度 | 用途 |
| --- | --- | --- |
| metric_name | metric ごと | accuracy、macro_f1、json_valid_rate など集計指標を識別する |
| scorer_name | metric ごと | どの case scorer から計算したかを固定する |
| scorer_version | metric ごと | 後から scorer 実装が変わっても比較条件を再現できる |
| reference_type | metric ごと | label、text、json、none のどれを参照したかを追跡する |
| aggregation | metric ごと | mean、macro_f1、all_constraints など集計方法を明示する |
| threshold | metric ごと | 1.0、range、null などの pass または fail 閾値を記録する |
| pass_rule | metric ごと | case pass と run pass の決め方を短い識別子で残す |
| metric_definition | metric ごと | prediction_path、required_fields、label_space、normalization、length_unit、constraint_ids など scorer の解釈条件を保存する |
| expected_output_format | prompt または metric | json、text、bullet_list など構造判定の前提を残す |
| output_contract_snapshot | prompt ごと | constraint_pass と format_valid の元になった制約集合を凍結する |
| evaluation_mode | metric ごと | auto、manual、hybrid を明示し、暫定指標を公式比較と分ける |

accuracy や macro_f1 を後から再集計するため、classification では normalized_prediction と normalized_reference を case 単位でも残す方がよい。extraction では missing_fields と mismatched_fields、constraint_pass では failed_constraints を残すと原因分析がしやすい。

request 00006 の sample prompt では、classification は `metadata.evaluation_reference.label` と `output_contract.prediction_path` / `label_space` を持ち、extraction は `metadata.evaluation_reference` と `output_contract.required_fields` を持ち、rewrite は `output_contract.constraint_ids` と machine-readable 制約を持つ形にそろえる。

## Config 管理と Model 管理への接続

役割の境界は次の 4 層に分ける。

1. prompt template: 単一の評価テンプレートを表す。
2. prompt set: 複数の prompt template を束ねる。カテゴリやタグで include できる。
3. model profile: provider 上の実モデル識別子、既定パラメータ、能力タグを持つ。
4. benchmark suite: どの model selection と prompt set を組み合わせ、どの比較条件で走らせるかを定義する。

関係は benchmark suite -> model selection -> prompt set -> prompt template の順に解決する。

- benchmark suite は model_selector と prompt_set_ids を持つ。
- model_selector は model registry から model_id 一覧を解決する。
- prompt_set は prompt_id 直指定、category 指定、tag 指定のいずれかで prompt template を集める。
- 実行時は prompt template の variables に各データセット行の値を束縛して prompt instance を作る。

generation parameters の優先順位は次を推奨する。

1. run ごとの明示 override
2. benchmark suite の generation_overrides
3. prompt template の recommended_generation_parameters
4. model profile の default_generation_parameters
5. provider adapter の内部既定値

この順にしておくと、通常は task ごとの推奨値を使いつつ、公平比較したい suite では上位で固定しやすい。

## 推奨ファイル構造例

```text
configs/
  benchmark_suites/
    local-three-tier-baseline-v1.toml
  model_registry/
    local-models-v1.toml
  prompt_sets/
    core-small-model-ja-v1.toml
  provider_profiles/
    local-default.toml
prompts/
  classification/
    contact-routing-v1.toml
  constrained_generation/
    followup-action-json-v1.toml
  extraction/
    invoice-fields-v1.toml
  rewrite/
    polite-rewrite-v1.toml
  short_qa/
    support-hours-answer-v1.toml
  summarization/
    meeting-notice-summary-v1.toml
```

provider ごとの接続情報は configs/provider_profiles に寄せ、model registry と prompts から分離した方が保守しやすい。

## request 00009: ロードマップ 3 の最小スライス

- sample prompt set の最小完成形は 6 カテゴリ各 1 prompt とし、core-small-model-ja-v1 は classification、extraction、rewrite、summarization、short_qa、constrained_generation を明示的な prompt_ids で固定する。
- reference_type が none の prompt でも [metadata.evaluation_reference] の空 table を持たせ、sample prompt の shape をそろえる。
- deterministic scorer が使う machine-readable 条件は output_contract と metadata.evaluation_reference に寄せ、storage は解釈せず snapshot を保存するだけにする。

## request 00004: provider 非依存 config 外部化

### provider 非依存境界

- cli/main.py は共通 CLI の入口として扱い、provider 固有 import、サブコマンド名、help 文言、応答 JSON の解釈を持たない。
- config/models.py と config/loader.py は共通スキーマ、外部ファイル読み込み、参照整合性検証だけを担当し、特定 provider 名、model_key、prompt_id、suite_id の既定値を埋め込まない。
- provider 名を列挙してよいのは、外部設定ファイルと providers 配下の factory、adapter、client に限る。

### ロードマップ 1 の最小スコープ

1. configs 配下の benchmark_suites、model_registry、prompt_sets、provider_profiles と prompts 配下の prompt 定義を外部ファイルから読める。
2. 共通 CLI が run コマンドで suite を指定して benchmark を実行できる。
3. 3 ランク各 1 モデルの初期比較を sample config として同梱できる。
4. loader、CLI、suite 解決の最小テストがそろい、in-memory stub への依存を外せる。

### 3 ランク各 1 モデルの表現

- 初期比較用 suite は explicit_model_keys で 3 モデルを固定し、比較対象が設定更新でぶれないようにする。
- model registry には tier:entry、tier:balanced、tier:quality のような capability tag を持たせ、将来は同じ tier に複数モデルを追加できるようにする。
- tier の補足情報が必要な場合は metadata に family や parameter_scale を持たせ、suite 側のスキーマは増やしすぎない。

### CLI と loader の実装契約

- 共通 CLI の最小形は local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1 とし、run_id は省略時に loader または CLI 側で補完する。
- 実装では依存追加を避けるため stdlib の tomllib を使い、外部設定形式は TOML を採用する。
- CLI は config.loader の単一入口で設定 bundle を受け取り、providers.factory のような provider 組み立て境界を経由して runner へ注入する。
- provider 固有の疎通確認が必要な場合は providers/<provider_id>/cli.py か providers/<provider_id>/diagnostics.py へ寄せ、request 00004 の最小スコープには含めない。

### TOML 例

```toml
provider_id = "ollama"

[connection]
base_url = "http://localhost:11434"
timeout_seconds = 30.0

[settings]
keep_alive = "5m"
```

```toml
[[models]]
model_key = "local.entry.gemma3"
provider_id = "ollama"
provider_model_name = "gemma3:latest"
capability_tags = ["local", "chat", "ja", "tier:entry"]

[models.metadata]
comparison_tier = "entry"
parameter_scale = "compact"

[[models]]
model_key = "local.balanced.qwen2_5"
provider_id = "ollama"
provider_model_name = "qwen2.5:7b"
capability_tags = ["local", "chat", "ja", "tier:balanced"]

[models.metadata]
comparison_tier = "balanced"
parameter_scale = "standard"

[[models]]
model_key = "local.quality.llama3_1"
provider_id = "ollama"
provider_model_name = "llama3.1:8b"
capability_tags = ["local", "chat", "ja", "tier:quality"]

[models.metadata]
comparison_tier = "quality"
parameter_scale = "extended"
```

```toml
suite_id = "local-three-tier-baseline-v1"
description = "3 ランク各 1 モデルで比較する初期 baseline"
prompt_set_ids = ["core-small-model-ja-v1"]
tags = ["baseline", "three-tier"]

[model_selector]
explicit_model_keys = [
  "local.entry.gemma3",
  "local.balanced.qwen2_5",
  "local.quality.llama3_1",
]

[generation_overrides]
temperature = 0.0
top_p = 0.95
max_output_tokens = 128
```

### テスト観点

- loader 正常系: config root 全体を読み込み、suite、prompt set、prompt、model、provider profile の参照が解決できる。
- loader 異常系: 重複 ID、欠落した prompt_set_id、欠落した model_key、未定義 provider_id を明示的にエラー化する。
- CLI: help と run が provider 固有語に依存せず、--config-root と --suite で benchmark 実行まで到達できる。
- 初期 suite: 3 モデルだけを解決し、各モデルが tier tag を持つことを確認する。

## Python dataclass 例

```python
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class PromptVariable:
    name: str
    type: Literal["string", "integer", "float", "boolean", "string_list"]
    required: bool = True
    description: str = ""
    default: Any | None = None
    example: Any | None = None
    validation: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationParameters:
    temperature: float | None = None
    top_p: float | None = None
    max_output_tokens: int | None = None
    stop: list[str] = field(default_factory=list)
    seed: int | None = None


@dataclass(slots=True)
class EvaluationMetadata:
    primary_metric: str
    secondary_metrics: list[str] = field(default_factory=list)
    reference_type: Literal["label", "text", "json", "none"] = "text"
    scorer: str = "exact_match"
    difficulty: Literal["starter", "standard", "advanced"] = "starter"
    language: str = "ja"
    expected_output_format: Literal["text", "json", "bullet_list"] = "text"


@dataclass(slots=True)
class PromptTemplateRecord:
    prompt_id: str
    version: str
    category: str
    title: str
    description: str
    system_message: str
    user_message: str
    variables: list[PromptVariable]
    recommended_generation_parameters: GenerationParameters = field(default_factory=GenerationParameters)
    tags: list[str] = field(default_factory=list)
    evaluation_metadata: EvaluationMetadata = field(default_factory=lambda: EvaluationMetadata(primary_metric="exact_match"))
    output_contract: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelProfile:
    model_id: str
    provider: str
    provider_model_name: str
    capability_tags: list[str] = field(default_factory=list)
    default_generation_parameters: GenerationParameters = field(default_factory=GenerationParameters)


@dataclass(slots=True)
class BenchmarkSuite:
    suite_id: str
    model_ids: list[str] = field(default_factory=list)
    prompt_set_ids: list[str] = field(default_factory=list)
    generation_overrides: GenerationParameters = field(default_factory=GenerationParameters)
    tags: list[str] = field(default_factory=list)
```

## TOML 構造例

```toml
suite_id = "local-small-baseline-v1"
description = "小型ローカルモデルの初期比較セット"
prompt_set_ids = ["core-small-model-ja-v1"]

[model_selector]
include_tags = ["local", "chat", "small"]

[generation_overrides]
temperature = 0.2
top_p = 0.95
max_output_tokens = 256
```

```toml
prompt_id = "contact-routing-v1"
version = "1"
category = "classification"
title = "問い合わせ分類"
description = "問い合わせ本文を事前定義ラベルのいずれかへ分類する"
system_message = """
あなたは問い合わせ分類の評価対象モデルです。
与えられたラベル一覧から最も適切なものを 1 つ選んでください。
"""
user_message = """
ラベル候補: {{labels}}
問い合わせ本文: {{input_text}}
出力は JSON で {"label": "..."} のみを返してください。
"""
tags = ["ja", "small-model-friendly", "json-output", "baseline"]

[[variables]]
name = "labels"
type = "string_list"
required = true
description = "利用可能な分類ラベル一覧"

[[variables]]
name = "input_text"
type = "string"
required = true
description = "分類対象の問い合わせ本文"

[recommended_generation]
temperature = 0.1
top_p = 0.9
max_output_tokens = 64

[evaluation_metadata]
primary_metric = "accuracy"
secondary_metrics = ["macro_f1"]
reference_type = "label"
scorer = "exact_match_label"
difficulty = "starter"
language = "ja"
expected_output_format = "json"

[output_contract]
type = "json_object"
required_keys = ["label"]
prediction_path = "label"
label_space = ["請求", "技術サポート", "契約", "その他"]
```

## 実装引き継ぎメモ

- prompt loader は prompt template と prompt set を分けて読み込めるようにする。
- model selector は tag ベース解決と explicit model_id 指定の両方を持つと運用しやすい。
- suite resolver は parameter merge の優先順位を 1 箇所で管理し、runner 側に分散させない。
- 初期実装では variables の型検証と output_contract の軽い検証だけあれば十分で、複雑なスキーマ検証は後段でもよい。

## リスクと今後の改善

- prompt ごとに推奨パラメータを持たせすぎると公平比較がぶれやすい。suite 側で固定しやすい設計を維持する必要がある。
- category が増えすぎると集計が読みにくくなる。初期は 5 から 6 個に絞り、必要なら tag で補う方がよい。
- system_message が長すぎると小型モデル差より文脈長耐性差が前面に出る。初期 corpus は短い指示を優先する。