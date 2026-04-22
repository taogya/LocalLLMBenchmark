---
request_id: "00012"
task_id: "00012-01"
parent_task_id: "00012-00"
owner: "solution-architect"
title: "design-secret-env-and-runtime-check"
status: "done"
depends_on: []
created_at: "2026-04-18T19:20:00+09:00"
updated_at: "2026-04-18T20:10:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/config/models.py"
  - "src/local_llm_benchmark/config/loader.py"
  - "src/local_llm_benchmark/providers/factory.py"
---

# 入力要件

- provider profile で API キー平文を避けたい。
- 現状構成の runtime readiness と確認方法も整理したい。
- 実装は行わず、progress に設計判断と具体的な変更指示を残したい。

# 整理した要件

- config 側は secret value ではなく環境変数名参照を保持し、provider profile をそのまま共有しても秘密情報が残らない形に寄せる。
- local server 用でも API キー不要ケースを壊さず、認証が必要な時だけ明示的に環境変数参照を宣言できる契約にする。
- `src/local_llm_benchmark/config` には provider 固有の secret 解決ロジックを持ち込まず、provider 非依存境界を守る。
- 実行確認は code readiness と environment readiness を分け、README と architecture doc に落とし込める最短フローへ整理する。

# 作業内容

- `configs/provider_profiles/openai-compatible-local.toml` に `connection.api_key = "local-dummy"` の平文例が残っていることを確認した。
- `src/local_llm_benchmark/providers/factory.py` が `connection.api_key` をそのまま `OpenAICompatibleClient` へ渡していること、`OpenAICompatibleClient` 自体は `api_key is None` の時に Authorization header を送らないことを確認した。
- `src/local_llm_benchmark/config/models.py` と `src/local_llm_benchmark/config/loader.py` は provider profile を generic な mapping として扱っており、現状でも provider 固有 key を dataclass や loader validation に持ち込んでいないことを確認した。
- `README.md` と `docs/architecture/benchmark-foundation.md` を確認し、OpenAI-compatible provider の存在は記載済みだが、secret の持ち方と runtime readiness の分離は未整理であることを確認した。
- `tests/cli/test_live_smoke.py` は Ollama 向けの opt-in live smoke であり、OpenAI-compatible local server の readiness を共通 CLI で直接診断する導線はまだ持っていないことを確認した。

# 判断

- OpenAI-compatible local server 用 profile の secret 契約は `connection.api_key_env` を採用し、config には API キー値を置かない方針を採る。
- API キーが不要な local server を壊さないため、`api_key_env` は任意項目とし、未指定時は Authorization header を送らない契約を維持する。
- ただし `api_key_env` を明示したのに環境変数が未設定または空文字の時は、無認証で続行せず factory で即時に `ValueError` を返す方が妥当である。secret 参照を宣言した時点で user は認証付き接続を意図しており、header を黙って落とすと設定ミスを見逃しやすいためである。
- `OPENAI_API_KEY` のような既定環境変数は自動参照しない。local server 向け profile から cloud 用 secret を誤送信しないため、profile に書かれた環境変数名だけを解決する。
- provider 非依存境界を守るため、環境変数解決と `api_key_env` の検証は `config/models.py` や `config/loader.py` ではなく `src/local_llm_benchmark/providers/factory.py` の OpenAI-compatible 分岐で扱う。
- readiness は「コードと config の結線が正しいか」と「外部 runtime が整っているか」で性質が違うため、README と architecture doc の両方で code readiness / environment readiness に分けて案内する。

# 成果

## 採用方針

- provider profile に保持するのは API キー値ではなく、環境変数名を表す `connection.api_key_env` とする。
- `connection.api_key_env` は OpenAI-compatible local server で認証が必要な時だけ設定する任意項目とする。
- `connection.api_key_env` が未指定なら Authorization header は送らない。これを key 不要 server の正式な契約とする。
- `connection.api_key_env` が指定されているのに参照先環境変数が未設定または空文字なら、factory で fail fast する。
- 旧 `connection.api_key` はこの request で廃止対象とし、OpenAI-compatible profile では受け付けない方針を推奨する。移行メッセージは `api_key_env` への切り替えを明示する。
- sample profile や README の例で使う環境変数名は `LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY` のような project-local 名に寄せ、`OPENAI_API_KEY` の再利用は勧めない。

## 実装指示

### configs/provider_profiles/openai-compatible-local.toml

- `connection.api_key` の平文例は削除する。
- sample profile の既定値は keyless local server に合わせ、`base_url` と `timeout_seconds` だけを残す。
- 認証が必要な server 向けの設定例はコメントで示し、`api_key_env = "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY"` のように環境変数名だけを書く。
- metadata の説明文にも「認証が必要な場合だけ `api_key_env` を追加する」ことを短く添える。

### src/local_llm_benchmark/config/models.py

- `ProviderProfile` の dataclass 構造は変えない。`connection` を generic mapping のまま保ち、OpenAI-compatible 固有の field は追加しない。
- secret 参照の型をここで一般化しない。今回のスコープでは provider profile の key 名で表現するだけで十分であり、汎用 secret framework を先に入れると責務が広がりすぎる。

### src/local_llm_benchmark/config/loader.py

- loader は TOML を `ProviderProfile.connection` へ写すだけに留め、環境変数の読み出しや `api_key_env` の検証は行わない。
- `config/*.py` は provider 非依存層なので、`openai_compatible` 固有 key 名や既定環境変数名を持ち込まない。
- 追加の検証が必要なら「mapping として読めるか」までに留め、secret 解決の成否は run 時の factory に委ねる。

### src/local_llm_benchmark/providers/factory.py

- OpenAI-compatible adapter の組み立て時に `connection.api_key_env` を読む helper を追加する。
- helper は次の優先順位で判定する。
  1. `connection.api_key` が存在したら `ValueError` で移行を促す。
  2. `connection.api_key_env` が未指定なら `None` を返す。
  3. `connection.api_key_env` が空でない文字列なら、その名前の環境変数を読む。
  4. 参照先が未設定または空文字なら `ValueError` を返す。
- `OpenAICompatibleClient` には解決済みの文字列だけを渡し、client 側は引き続き `api_key is None` の時に Authorization header を省略する。
- `OPENAI_API_KEY` などの暗黙 fallback は追加しない。

### README.md

- OpenAI-compatible local server の説明に「認証が必要なら provider profile へ `api_key_env` を書き、値は環境変数で渡す」ことを短く追記する。
- key 不要 server では `api_key_env` を省略すると Authorization なしで送ることを明記する。
- 実行確認フローは user 向けに次の 2 段に分けて短く追記する。
  - code readiness: install 後に `local-llm-benchmark suites --config-root configs` を実行し、config と CLI が読めることを確認する。
  - environment readiness: local server 起動、model alias 準備、必要なら環境変数 export の後に `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1` を実行する。

### docs/architecture/benchmark-foundation.md

- secret 解決の責務境界を追記する。config loader は secret を読まず、provider factory が明示的な env 参照だけを解決することを書く。
- OpenAI-compatible provider の認証契約として「`api_key_env` 未指定なら無認証」「指定済みで未解決なら configuration error」を明文化する。
- runtime readiness を code readiness と environment readiness に分け、失敗時の切り分け観点を短く整理する。

## runtime readiness の整理

### code readiness

- 目的は「repo と config が実行入口まで正しく結線されているか」の確認であり、外部 server や secret を前提にしない。
- user 向け最短フローは install 後に `local-llm-benchmark suites --config-root configs` を実行することとする。
- この段階で確認したいことは、TOML 読み込み、prompt / suite / provider profile の参照整合、CLI 入口の健全性である。
- 実装担当の検証では、`tests/config/test_loader.py` と `tests/providers/test_factory.py`、`tests/providers/test_openai_compatible_client.py` の更新も併せて行い、secret 契約の退行を防ぐ。

### environment readiness

- 目的は「外部 runtime が実際に推論要求を受けられるか」の確認であり、base_url、auth、model alias、server 稼働状態を含む。
- user 向け最短フローは次の順を推奨する。
  1. provider profile の `base_url` を local server に合わせる。
  2. model registry の `provider_model_name` が server 側で利用可能な alias と一致していることを確認する。
  3. profile に `api_key_env` を書いた場合だけ、対応する環境変数を export する。
  4. `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1` を実行する。
- 切り分けの目安は次のとおりとする。
  - adapter 組み立て前後で `api_key_env` 未解決エラーが出る: environment readiness の不足。
  - 接続エラーが出る: server 未起動または base_url 不一致。
  - 401 / 403 相当の応答が出る: auth mismatch。
  - model not found 系の応答が出る: model alias 不一致。
- provider 非依存 CLI に新しい readiness サブコマンドはこの request では追加しない。まずは docs と既存の `suites` / `run` で最短導線を固定する。

## 残リスク

- `connection.api_key` を hard reject すると既存の custom profile とは非互換になる。今回は安全側を優先するが、利用者が多い場合は別 request で移行期間を設ける余地がある。
- OpenAI-compatible local server は auth 要不要や error payload の形が実装ごとに揺れるため、README の最短フローだけでは原因切り分けが不足する可能性がある。
- 現状は provider 共通の runtime diagnostics を持たないため、environment readiness の確認は docs と実行結果の読解に依存する。
- 将来別 provider でも secret 参照が必要になった場合、`api_key_env` を provider ごとに増やすだけでは命名と実装が散る可能性がある。

# 次アクション

- programmer が sample profile、factory、README、architecture doc をこの方針で更新し、関連 unit test の期待値も `api_key_env` 契約へ合わせる。
- reviewer が provider 非依存境界、`api_key_env` 未設定時の keyless 契約、未解決時の fail fast、README の readiness 導線が実装と一致しているかを確認する。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- configs/provider_profiles/openai-compatible-local.toml
- src/local_llm_benchmark/config/models.py
- src/local_llm_benchmark/config/loader.py
- src/local_llm_benchmark/providers/factory.py

# 設計対象

- OpenAI-compatible local server 用 provider profile の secret 参照契約。
- provider 非依存 config 層と provider factory の責務境界。
- user が最短で run 可否を判定するための runtime readiness の分解。

# 設計判断

- secret は config に値を置かず、必要時だけ `connection.api_key_env` で環境変数名を参照する。
- key 不要 server の正式契約は「`api_key_env` を書かない」であり、この時は Authorization header を送らない。
- `api_key_env` を明示したのに解決できない場合は、無認証送信へ降格せず factory で fail fast する。
- loader は provider 非依存のまま保ち、secret 解決は OpenAI-compatible provider 組み立て境界に閉じ込める。
- readiness 確認は `suites` を code readiness、`run` を environment readiness の最短導線として整理する。

# 影響範囲

- sample provider profile の記法が `api_key` から `api_key_env` 前提へ変わる。
- OpenAI-compatible provider の adapter build 時 validation が secret 参照前提に変わる。
- README と architecture doc に認証契約と readiness の分離が追加される。
- 関連 unit test の期待値が `api_key` 受理から `api_key_env` 契約へ変わる。

# リスク

- 既存 custom profile との非互換。
- provider 共通 diagnostics 未整備による切り分け負荷。
- 将来の複数 provider で secret 参照ルールが散る可能性。

# 改善提案

- ほかの provider でも env 参照が増えた段階で、`env:VAR_NAME` のような generic secret reference 形式を別 request で検討するとよい。
- OpenAI-compatible local server 向けの opt-in live smoke あるいは diagnostics は、共通 CLI へ provider 固有知識を持ち込まない形で別 request に切り出すのがよい。
- README では最短フローだけを保ち、詳細な切り分け例は将来 provider 別 docs に逃がすと初心者向け導線を維持しやすい。