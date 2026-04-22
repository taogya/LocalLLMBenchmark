---
request_id: "00010"
task_id: "00010-01"
parent_task_id: "00010-00"
owner: "solution-architect"
title: "design-openai-compatible-provider"
status: "done"
depends_on: []
created_at: "2026-04-18T14:35:00+09:00"
updated_at: "2026-04-18T16:45:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/config/models.py"
  - "src/local_llm_benchmark/config/loader.py"
  - "src/local_llm_benchmark/providers"
  - "src/local_llm_benchmark/providers/base.py"
  - "src/local_llm_benchmark/providers/factory.py"
  - "configs/provider_profiles"
  - "tests/providers"
---

# 入力要件

- ロードマップ 4 の最初の provider 拡張として OpenAI-compatible local provider を設計したい。
- 現在は Ollama のみ実装されており、factory も `provider_id == "ollama"` の dispatch だけを持つ。
- LM Studio / vLLM / llama.cpp server 系へ広く載せやすい最小実装境界を先に固定したい。
- provider 非依存ファイルへ OpenAI 固有 help やコマンドを持ち込まず、依存追加なしで進めたい。

# 整理した要件

- provider 非依存境界を崩さない最小実装境界を定義する。
- OpenAI vendor 固有実装ではなく、OpenAI-compatible local server の共通面だけを扱う。
- adapter / client / factory / provider profile / sample docs / tests の追加方針を、programmer がそのまま実装できる粒度まで落とす。
- 今回は local provider 向けの最小スライスに留め、複数バックエンド同時利用や拡張 API は後続へ送る。

# 作業内容

- README、architecture docs、providers/base.py、providers/factory.py、Ollama adapter/client、provider profile sample、Ollama adapter test を確認し、既存の provider 境界と profile schema の前提を整理した。
- progress/project-master/00010-00-roadmap-4-openai-compatible-provider.md と config/models.py、config/loader.py を確認し、現在の `provider_id` が「profile 識別子」と「adapter 種別」を兼ねていることを確認した。
- 既存の solution-architect progress を見て、設計判断、影響範囲、リスク、改善提案まで含む done 形式にそろえた。

# 判断

- 最小実装の `provider_id` は `openai_compatible` を推奨する。`openai` だと将来の公式 OpenAI provider と意味が衝突しやすく、`lmstudio` や `vllm` だと単一ツール専用に見えるため避ける。
- ディレクトリ名は `src/local_llm_benchmark/providers/openai_compatible/` とし、`adapter.py` と `client.py` を Ollama と同じ粒度で並置する。責務分割は既存の Ollama 実装を踏襲し、adapter は共通 request/response の変換、client は HTTP 通信と JSON 応答の検証に限定する。
- API 形の最小サポートは `POST {base_url}/chat/completions` のみで十分と判断した。現行 benchmark core は system/user 2 message の単発推論しか要求しておらず、`responses`、legacy `completions`、`/models`、streaming、tools、JSON mode は不要である。
- provider profile に `model` は持たせない。モデル名は既存設計どおり model registry の `provider_model_name` に残し、provider profile は接続先と送信方針だけを持つ。これを崩すと比較軸が connection と model で混ざる。
- provider profile の最小 schema は `provider_id`、`connection.base_url`、任意の `connection.api_key`、任意の `connection.timeout_seconds`、任意の `metadata` で足りる。`base_url` は `http://localhost:1234/v1` のように API prefix を含む root とし、client 側は `/chat/completions` を足す。v1 では必須追加項目は設けない。
- `GenerationSettings.seed` は core 側で保持し続けるが、OpenAI-compatible provider v1 では無条件送信しない方針を推奨する。seed の受理可否がローカル server 実装ごとに揺れやすく、最小スライスでは相互運用性を優先する。
- factory は大きく作り替えず、`_build_provider_adapter()` に `openai_compatible` 分岐を追加する最小変更でよい。ただし provider ごとの validation と constructor 呼び出しは helper 関数へ切り出し、if 分岐の肥大化だけは抑える。
- sample profile は追加してよいが、既定 suite や既存 Ollama sample を切り替えない。README と architecture doc には「OpenAI-compatible local server を provider profile で接続できる」ことだけを最小限追記し、LM Studio / vLLM / llama.cpp ごとの個別コマンドは持ち込まない。
- テストは live smoke より unit test を優先する。local OpenAI-compatible server は起動方法のばらつきが大きいため、初手は adapter/client/factory の pure な検証で境界を固める方がよい。
- 将来 LM Studio / vLLM / llama.cpp server を吸収する主軸は、「同一 adapter/client に対して接続先だけを差し替える」ことに置く。一方で複数 OpenAI-compatible endpoint を同時利用したくなった時は、現在の `provider_id` 一意制約が先にボトルネックになる。

# 成果

## 推奨設計

### 1. provider_id とディレクトリ名

- provider_id: `openai_compatible`
- ディレクトリ: `src/local_llm_benchmark/providers/openai_compatible/`
- 追加ファイル:
  - `adapter.py`
  - `client.py`

命名理由:

- `openai_compatible` は vendor 名ではなく protocol family を表せる。
- LM Studio / vLLM / llama.cpp server のいずれにも寄せすぎない。
- 将来、公式 OpenAI provider を別物として追加する余地を残せる。

### 2. client / adapter の責務分割

- `OpenAICompatibleClient`
  - `urllib` ベースで HTTP POST を送る。
  - `Authorization: Bearer ...` を api_key がある時だけ付与する。
  - HTTP error、接続 error、JSON decode error を `ProviderConnectionError` / `ProviderResponseError` へ変換する。
  - `chat_completions(...)` の low-level API を持ち、payload と raw JSON object を扱う。
- `OpenAICompatibleAdapter`
  - `InferenceRequest` から messages 配列を作る。
  - `request.model.provider_model_name` を `model` に入れる。
  - v1 では `temperature`、`top_p`、`max_tokens`、`stop` だけを request payload へ写す。
  - raw response の `choices[0].message.content`、`usage`、`finish_reason` を共通 `InferenceResponse` に正規化する。
  - server 固有の補助情報は `provider_metadata` に閉じ込める。

### 3. API 形の最小サポート

- 最小サポートは chat completions だけで十分。
- リクエストは `stream = false` 固定。
- 対象 endpoint は `POST {base_url}/chat/completions`。
- v1 の payload 最小項目:
  - `model`
  - `messages`
  - `stream`
  - 任意の `temperature`
  - 任意の `top_p`
  - 任意の `max_tokens`
  - 任意の `stop`
- v1 で見送るもの:
  - `responses` API
  - legacy `completions`
  - streaming
  - tools / function calling
  - `response_format`
  - `seed` の無条件送信
  - model listing / healthcheck endpoint

レスポンスの最小期待 shape:

- `choices` が配列
- 先頭 choice の `message.content` が文字列
- `usage.prompt_tokens` / `usage.completion_tokens` / `usage.total_tokens` はあれば使い、なければ `None`
- `finish_reason` は先頭 choice から拾う

### 4. provider profile の最小 schema

`model` は provider profile ではなく model registry に置く。profile は connection 専用に保つ。

最小 shape:

```toml
provider_id = "openai_compatible"

[connection]
base_url = "http://localhost:1234/v1"
timeout_seconds = 30.0
api_key = "local-dummy"

[metadata]
description = "OpenAI-compatible local server 用の sample profile。"
```

補足:

- `api_key` は任意。未設定時は Authorization header を送らない。
- `timeout_seconds` は任意で、既定値 30.0 を factory 側で補完する。
- `base_url` は `/v1` を含む API root とする。これで `api_base_path` のような追加キーを避けられる。
- `settings` は v1 では不要。将来 `extra_headers`、`emit_seed`、`response_format_mode` のような差分吸収点が必要になった時だけ増やす。

### 5. factory 追加方針

- `build_provider_adapters()` の public interface は維持する。
- `_build_provider_adapter()` に `openai_compatible` 分岐を追加する。
- ただし branch 内の処理は `_build_ollama_adapter(...)`、`_build_openai_compatible_adapter(...)` のような helper に寄せる。
- validation ルール:
  - `connection.base_url`: 必須の非空文字列
  - `connection.timeout_seconds`: 任意の float 互換
  - `connection.api_key`: 任意の非空文字列。未指定は許容
- provider 非依存層へ新しい import や help 文言は持ち込まない。

### 6. sample profile と docs の最低限

- sample profile は `configs/provider_profiles/openai-compatible-local.toml` を追加する。
- README の最小追記は次の 2 点で足りる。
  - ロードマップ 4 で OpenAI-compatible local provider を追加対象にしたこと
  - provider profile で接続先を切り替えられること
- architecture doc の最小追記は次の 2 点で足りる。
  - `openai_compatible` provider は `/chat/completions` のみを v1 対象にすること
  - LM Studio / vLLM / llama.cpp server 系は接続先差し替えで吸収する方針であること
- サーバ個別の起動コマンドや CLI 手順はこの request の範囲外とする。

### 7. テスト観点

- `tests/providers/test_openai_compatible_adapter.py`
  - system/user message の組み立て
  - `choices[0].message.content` からの正規化
  - usage / finish_reason / provider_metadata の取り出し
  - content 欠落時の `ProviderResponseError`
- `tests/providers/test_openai_compatible_client.py`
  - `/chat/completions` への POST
  - api_key ありなしでの header 分岐
  - HTTPError / URLError / JSONDecodeError の変換
- `tests/providers/test_factory.py` または既存 factory 周辺 test
  - `provider_id = "openai_compatible"` で adapter が組み上がる
  - `base_url` 欠落や `timeout_seconds` 型不正で `ValueError`
- `tests/config/test_loader.py`
  - sample profile 追加後も config bundle が崩れない
  - provider_id の参照整合性が維持される

live smoke は v1 の必須条件にしない。

## 最小実装方針

1. `providers/openai_compatible/adapter.py` と `client.py` を追加する。
2. `providers/factory.py` に `openai_compatible` 分岐と helper を追加する。
3. `configs/provider_profiles/openai-compatible-local.toml` を sample として追加する。
4. README と architecture doc に server 非依存の最小説明だけを追記する。
5. adapter / client / factory / loader の unit test を追加し、既存 Ollama default の挙動は変えない。

## リスクと後続余地

- 現在の config schema は `provider_id` が profile 識別子と adapter 種別を兼ねるため、`openai_compatible` を 1 つしか持てない。LM Studio と vLLM を同一 run で並べたい場合は、後続で `provider_kind` と `provider_profile_id` の分離が必要になる。
- local OpenAI-compatible server は seed、usage、finish_reason、content shape の実装差がある。v1 は共通最小面だけを扱い、差分吸収の設定は後ろ倒しにする。
- model 名は各 server のロード済み alias に依存するため、sample model registry をこの task で固定しすぎると汎用性を損ねる。まずは profile と adapter 境界だけを stable にする方がよい。
- 将来必要になった時の拡張順は、`seed` opt-in、`response_format` opt-in、複数 endpoint 対応、healthcheck / live smoke、`responses` API 対応の順を推奨する。

# 次アクション

- programmer が `openai_compatible` adapter / client / factory / sample profile / tests を最小構成で実装する。
- reviewer が provider 非依存境界、README / architecture の記述粒度、`provider_id` 一意制約のリスク説明が十分かを確認する。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/config/models.py
- src/local_llm_benchmark/config/loader.py
- src/local_llm_benchmark/providers
- src/local_llm_benchmark/providers/base.py
- src/local_llm_benchmark/providers/factory.py
- configs/provider_profiles
- tests/providers

# 設計対象

- ロードマップ 4 の最初の provider 拡張として追加する OpenAI-compatible local provider の命名、責務分割、最小 API 境界。
- provider profile、factory、sample docs、tests をどの粒度まで v1 で持つか。
- LM Studio / vLLM / llama.cpp server を将来どのように吸収するか。

# 設計判断

- provider family を表す `openai_compatible` を v1 の provider_id に採用する。
- adapter/client の粒度は Ollama 実装と合わせ、共通 dataclass と Protocol は変えない。
- chat completions の非 streaming だけを v1 の正式対象とし、互換差分が大きい API は見送る。
- model は model registry、connection は provider profile という責務分割を維持する。
- factory は最小変更で拡張しつつ、builder helper で provider ごとの差分を局所化する。
- docs と sample は server 非依存の最小説明に留め、個別ツールの手順書は追加しない。

# 影響範囲

- `src/local_llm_benchmark/providers` 配下に OpenAI-compatible provider 実装が追加される。
- `src/local_llm_benchmark/providers/factory.py` に dispatch と validation helper が追加される。
- `configs/provider_profiles` に sample profile が追加される。
- `README.md` と `docs/architecture/benchmark-foundation.md` に provider 拡張方針の最小説明が追加される。
- `tests/providers` と `tests/config` に OpenAI-compatible provider 用の unit test が追加される。

# リスク

- `provider_id` 一意制約のままでは、複数の OpenAI-compatible endpoint を同時に benchmark できない。
- seed や usage の互換差分を v1 で吸収しすぎると、設定項目と分岐が急増する。
- sample config へ server 固有モデル名を入れすぎると、README の再現性は上がっても汎用性が落ちる。

# 改善提案

- 次の provider 拡張が見えた段階で、`provider_kind` と `provider_profile_id` の分離を検討するとよい。
- OpenAI-compatible provider が安定したら、server 固有差分を `settings` の feature flag で吸収する前に、まず互換差分一覧を docs に整理すると実装肥大化を防げる。
- live smoke を追加する場合は LM Studio など特定ツール前提にせず、環境変数で base_url と api_key を差し替えられる opt-in 方式にするのが安全である。