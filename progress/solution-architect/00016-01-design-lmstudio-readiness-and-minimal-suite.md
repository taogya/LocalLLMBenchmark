---
request_id: "00016"
task_id: "00016-01"
parent_task_id: "00016-00"
owner: "solution-architect"
title: "design-lmstudio-readiness-and-minimal-suite"
status: "done"
depends_on: []
created_at: "2026-04-18T23:40:00+09:00"
updated_at: "2026-04-19T00:25:00+09:00"
related_paths:
  - "progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/lmstudio"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "configs/model_registry"
  - "configs/prompt_sets"
  - "configs/benchmark_suites"
  - "tests/cli/test_live_smoke.py"
---

# 入力要件

- LM Studio CLI の install / get / load / server start を前提に、現状の OpenAI-compatible スクリプトで不足があるか整理したい。
- OpenAI-compatible の最小 suite、model alias 方針、live smoke の最小境界を決めたい。
- strict / tolerant split と sentence_count explainability が今回必須かも判定したい。
- provider 非依存層へ provider 固有 subcommand や既定 ID を持ち込まず、docs と config の最小追加で済むならその方針を優先したい。

# 整理した要件

- LM Studio readiness は「インストールできる」ではなく、「CLI が使え、モデル alias を固定し、OpenAI-compatible endpoint で benchmark を実行できる」までを 1 本の導線として文書化する必要がある。
- 現行の OpenAI-compatible 実装は `/chat/completions` の最小 client なので、今回の論点は provider core の拡張ではなく、環境準備を利用者が迷わない docs / config / smoke の設計に寄せるべきである。
- minimal suite は provider 比較の本番系ではなく readiness と最小疎通確認を主目的にし、モデル identity を alias で抽象化して config 変更量を抑える。
- strict / tolerant split と sentence_count explainability は evaluation semantics の拡張なので、今回の readiness 導線を成立させる最小条件かどうかで切り分ける。

# 作業内容

- 指定された README、architecture doc、provider profile、model registry、benchmark suite、prompt set、3 つの prompt、OpenAI-compatible client、live smoke を確認し、現行の責務境界と最小変更候補を整理した。
- progress/project-master/00016-00-lmstudio-setup-and-openai-compatible-minimum-suite.md に加え、progress/solution-architect/00010-01-design-openai-compatible-provider.md、progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md、関連 progress を確認し、OpenAI-compatible 拡張と strict metric の既存判断を引き継いだ。
- docs/ollama/README.md と documentation / progress ルールを確認し、今回の文書は provider 固有 docs 1 枚、config 追加、必要なら opt-in smoke までに留める方針でまとめた。

# 判断

## 1. LM Studio readiness 文書で最低限書くべき flow

- 新しい文書は 1 枚で足りる。最小案は `docs/lmstudio/README.md` を追加し、root README からリンクする。
- 記載順は次で固定する。
  - LM Studio を install する。`lms` は同梱 CLI であることを明記する。
  - 一度だけ LM Studio 本体を起動する。CLI 利用前の初期化として必須であることを明記する。
  - `lms get <model_key>` で使うモデルを取得する。
  - `lms server start` で local server を起動する。既定の OpenAI-compatible base_url は `http://localhost:1234/v1` と書く。
  - `lms load <model_key> --identifier llmb-minimal-chat` でメモリロードし、API 呼び出し用 alias を固定する。
  - `lms server start` は model load を代替しないことを明記する。load を明示しない限り benchmark 側は未ロード error を受ける前提である。
  - 任意の確認として `GET /v1/models` で alias が見えることを確認してから、`local-llm-benchmark suites` と `run --suite openai-compatible-minimal-v1` を実行する流れへつなぐ。
- alias は docs 側の人間向け手順に閉じ込め、provider 非依存 CLI に LM Studio 固有コマンドを増やさない。benchmark 側が知るのは `provider_model_name = "llmb-minimal-chat"` だけでよい。

## 2. 現行スクリプトに必須のコード変更があるか

- src/local_llm_benchmark/providers/openai_compatible/client.py への必須変更はない。
- 現行 client は `POST /chat/completions` だけを使い、未ロードや未準備時の HTTP error を `ProviderResponseError` として返す。これは current architecture の責務境界と一致しており、今回の readiness request のために `/models` healthcheck や LM Studio 専用 error ハンドリングを provider core へ足す必要はない。
- したがって必須範囲は docs / config で足りる。live smoke を入れる場合だけ tests/cli/test_live_smoke.py を更新すればよく、src 側は据え置きでよい。
- configs/provider_profiles/openai-compatible-local.toml も既に `http://localhost:1234/v1` を向いているため、必須変更はない。説明文を軽く補強するかは任意である。

## 3. OpenAI-compatible minimal suite の最小構成

- モデル数は 1 でよい。目的は provider readiness と最小 run 完走確認であり、現段階で multi-model 比較まで広げる必要はない。
- prompt 数は 3 とし、既存 prompt をそのまま再利用する。
  - `contact-routing-v1`
  - `invoice-fields-v1`
  - `support-hours-answer-v1`
- この 3 本を選ぶ理由は、classification、strict JSON extraction、short_qa を 1 本ずつ押さえつつ、出力量と解釈コストが低く、rewrite / summarization / constrained_generation に伴う strict / tolerant 論点を今回の readiness から切り離せるためである。
- suite は新規追加とし、既存の `local-three-tier-baseline-v1` と `core-small-model-ja-v1` は変更しない。既定 sample を壊さないためである。
- prompt 参照は新しい provider-neutral prompt set 1 本でまとめる案を推奨する。命名は `minimal-readiness-ja-v1` がよい。prompt 自体は provider 非依存なので `openai-compatible` を prompt set 名へ持ち込まない方が再利用しやすい。
- suite id は `openai-compatible-minimal-v1` を推奨する。これは provider 固有の導線であることを docs と smoke で見分けやすいためである。
- model registry は alias-backed な 1 モデルを追加する。model key は actual model 名を装うより、用途を表す `local.openai_compatible.readiness` を推奨する。今回の目的が readiness slot だからである。
- `provider_model_name` は固定 alias `llmb-minimal-chat` を推奨する。LM Studio 上では `lms load ... --identifier llmb-minimal-chat` を使い、実際の backing model 名を config から切り離す。
- suite の generation は既存 baseline に揃え、`temperature = 0.0`、`top_p = 0.95`、`max_output_tokens = 128`、`seed = 7` を置いてよい。OpenAI-compatible v1 が `seed` を送らなくても config 上の一貫性は保てる。

## 4. live smoke を今回入れるべきか

- 入れる方がよい。ただし opt-in の別 smoke とし、provider core ではなく test 層に閉じ込める。
- 理由は、今回の request が docs と config の導線整備であり、実環境 drift を一番早く検知できるのが suites -> run -> report の live smoke だからである。
- 最小案は tests/cli/test_live_smoke.py に OpenAI-compatible 用の opt-in test class を追加し、既存 Ollama smoke の既定挙動は変えない。
- env var は `LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE` を推奨する。Ollama の既存 opt-in と分離でき、どちらを回すか明確になる。
- suite_id は `openai-compatible-minimal-v1` に固定する。
- 準備条件は次で十分である。
  - LM Studio を一度起動済みである。
  - `lms server start` で `http://localhost:1234/v1` が応答する。
  - `lms load <model_key> --identifier llmb-minimal-chat` を実行済みである。
  - profile が `api_key_env` を使う場合だけ、対応する環境変数が export 済みである。
- skip 条件は次でよい。
  - opt-in env var が未設定。
  - `openai_compatible` profile が見つからない、または base_url が不正。
  - `GET /v1/models` に接続できない。
  - `/v1/models` に required alias `llmb-minimal-chat` が見つからない。
  - profile が `api_key_env` を要求しているのに環境変数が未設定または空文字。
- `/v1/models` の確認は test 内の最小 HTTP 呼び出しで足りるため、client.py へ list-models API を追加する必要はない。

## 5. strict / tolerant split と sentence_count explainability は今回必須か

- 必須ではない。defer が妥当である。
- 理由は 3 つある。
  - request 00014 で current strict metric の読み方と defer 優先度が既に整理されている。
  - 今回選ぶ minimal suite は rewrite を含まず、sentence_count heuristic の explainability gap に依存しない。
  - strict / tolerant split は evaluation semantic と report interpretation の拡張であり、LM Studio readiness 導線という今回の最小目的を越える。
- 今回やるべきことは strict scorer を変えることではなく、README と LM Studio docs で current benchmark が strict JSON / strict contract 前提であることを維持したまま、OpenAI-compatible 用の最小実行経路を追加することである。

## 6. Bonsai 8B が取れない場合の fallback 方針

- fallback は config 分岐ではなく alias 運用で吸収する方針を推奨する。
- docs 上の第一候補は Bonsai 8B を例示してよいが、config には Bonsai 固有名を埋め込まない。利用者は別の instruct/chat model を同じ alias `llmb-minimal-chat` で load すれば、suite と smoke をそのまま再利用できる。
- これにより `configs/provider_profiles/openai-compatible-local.toml`、suite id、prompt set、model selection を変えずに fallback できる。
- ただしこの alias-backed 運用は readiness には向く一方、run 間で backing model が変わると厳密な model comparison には向かない。したがって docs には「この minimal suite は readiness 用であり、正式比較をしたい場合は actual model ごとに別 model_key を切る」と短く明記した方がよい。
- fallback 先は「既に手元で取得済み、かつ日本語短文応答と JSON 出力ができる instruct model」と定義するのが最小で安全である。catalog 固有の第二候補名を config へ固定する必要はない。

# 成果

- LM Studio readiness は docs 1 枚、alias 固定、server start と load の明示分離、`/v1/models` 確認、suite 実行までを 1 本の flow にする設計で固めた。
- OpenAI-compatible minimal suite は「1 model x 3 prompts」の alias-backed readiness slot とし、既存 baseline や provider core を触らずに config 追加で載せる方針で固めた。
- 必須変更は docs / config に限定し、src 側は据え置き、live smoke は test 層の opt-in 追加に留める境界を確定した。
- strict / tolerant split と sentence_count explainability は今回の blocker ではなく、request 00014 の結論どおり後続へ defer する判断を残した。
- Bonsai 8B fallback は alias 維持で吸収し、minimal suite を readiness 専用と位置付ける方針を確定した。

# 次アクション

- programmer は docs / config / smoke の最小変更で実装し、provider core には LM Studio 固有処理を追加しない。
- reviewer は LM Studio 導線、alias-backed readiness slot、smoke の skip 条件、defer 理由が project-master の前提と整合するかを確認する。

# programmer への具体的な変更指示

- `docs/lmstudio/README.md` を追加し、install、first run、`lms get`、`lms server start`、`lms load --identifier llmb-minimal-chat`、`/v1/models` 確認、`local-llm-benchmark run --suite openai-compatible-minimal-v1` までを短く書く。
- `README.md` に LM Studio readiness doc へのリンクと、OpenAI-compatible minimal suite の実行例を最小追記する。既存 Ollama sample の既定導線は変えない。
- `docs/architecture/benchmark-foundation.md` の readiness 説明へ、OpenAI-compatible local server では server start と model alias load を明示的に分けること、minimal suite は readiness 用であることを短く追記する。
- `configs/provider_profiles/openai-compatible-local.toml` は原則そのまま使う。必要なら metadata の説明だけを補強し、base_url や secret 方針は変えない。
- `configs/model_registry` に OpenAI-compatible readiness 用の 1 モデルを追加する。実装先は dedicated file を推奨し、`model_key = "local.openai_compatible.readiness"`、`provider_id = "openai_compatible"`、`provider_model_name = "llmb-minimal-chat"` とする。
- `configs/prompt_sets/minimal-readiness-ja-v1.toml` を追加し、`contact-routing-v1`、`invoice-fields-v1`、`support-hours-answer-v1` の 3 prompt を束ねる。
- `configs/benchmark_suites/openai-compatible-minimal-v1.toml` を追加し、上記 prompt set と `local.openai_compatible.readiness` を参照する。generation overrides は baseline と同じ `temperature = 0.0`、`top_p = 0.95`、`max_output_tokens = 128`、`seed = 7` を置く。
- `src/local_llm_benchmark/providers/openai_compatible/client.py` は変更しない。未ロード error の扱いは docs と smoke 前提で吸収する。
- `tests/cli/test_live_smoke.py` に OpenAI-compatible 用の opt-in smoke を追加する場合は、env var を `LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE`、suite id を `openai-compatible-minimal-v1` にし、`/v1/models` で alias `llmb-minimal-chat` を確認してから既存と同じ suites -> run -> report を回す。
- live 実行を行った場合は、programmer progress に actual backing model 名を明記する。alias-backed slot だけでは run の厳密な model identity が残りにくいためである。

# 設計対象

- LM Studio CLI readiness 文書の最小責務と導線。
- OpenAI-compatible minimal suite の model / prompt / alias 境界。
- live smoke を test 層へ追加する場合の最小条件。
- strict / tolerant split と Bonsai fallback を今回どこまで含めるか。

# 設計判断

- docs は provider 固有の 1 ファイル追加で足りる。
- minimal suite は 1 model x 3 prompts の readiness 専用 slot とする。
- alias `llmb-minimal-chat` を固定し、backing model は LM Studio docs 側で差し替え可能にする。
- src の OpenAI-compatible client は据え置き、必要なら smoke だけを追加する。
- strict / tolerant split と sentence_count explainability は defer する。

# 影響範囲

- `README.md`
- `docs/architecture/benchmark-foundation.md`
- `docs/lmstudio/README.md`
- `configs/model_registry`
- `configs/prompt_sets`
- `configs/benchmark_suites`
- `tests/cli/test_live_smoke.py`

# リスク

- alias-backed readiness slot は fallback しやすい反面、run 間で backing model が変わると厳密な model comparison には向かない。
- current config schema は `openai_compatible` profile を 1 つしか持てないため、LM Studio と別 OpenAI-compatible endpoint を同時比較する用途には広がらない。
- smoke を入れる場合、`/v1/models` の応答 shape 差分は test 側で吸収する必要がある。

# 改善提案

- OpenAI-compatible benchmark を readiness 以上へ広げる段階で、actual backing model 名を run metadata や docs に残す運用を追加すると比較解釈が安定する。
- 複数 OpenAI-compatible endpoint を並べたくなった段階で、`provider_kind` と profile 識別子の分離を検討するとよい。
- strict / tolerant split を進める場合は今回の suite を増やすのではなく、別 request で metric taxonomy と prompt taxonomy を分けて扱う方がよい。
