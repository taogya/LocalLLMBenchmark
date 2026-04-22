---
request_id: "00017"
task_id: "00017-01"
parent_task_id: "00017-00"
owner: "solution-architect"
title: "design-provider-loading-policy-and-doc-harmonization"
status: "done"
depends_on: []
created_at: "2026-04-19T01:05:00+09:00"
updated_at: "2026-04-19T03:15:00+09:00"
related_paths:
  - "progress/project-master/00017-00-assess-provider-loading-policy-and-harmonize-docs.md"
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "docs/ollama/README.md"
  - "docs/ollama/api-check.md"
  - "docs/lmstudio/README.md"
  - "configs/provider_profiles/local-default.toml"
  - "configs/provider_profiles/openai-compatible-local.toml"
  - "src/local_llm_benchmark/providers/ollama/client.py"
  - "src/local_llm_benchmark/providers/ollama/adapter.py"
  - "src/local_llm_benchmark/providers/openai_compatible/client.py"
  - "src/local_llm_benchmark/benchmark/runner.py"
---

# 入力要件

- Ollama と LM Studio のロード運用を、現行コードと公式仕様の両面から再整理する。
- 現構成の妥当性、docs で明示すべき点、provider docs の統一方針、defer 項目を固める。
- 実装は行わず、programmer がそのまま docs を更新できる具体指示を残す。

# 要件整理

- runner は model -> prompt の順で逐次実行し、並列実行はしない。
- Ollama は provider profile の settings.keep_alive を chat payload の keep_alive にそのまま渡す。
- OpenAI-compatible client は ttl を送らず、LM Studio 固有 endpoint も使わない。
- LM Studio には JIT loading、Idle TTL、Auto-Evict という server 側の既定ロード政策があり、手動の lms load はそれと別系統の explicit load である。
- 現在の openai-compatible-minimal-v1 と llmb-minimal-chat alias は readiness 専用 slot として読むのが自然で、正式比較向けの一般政策とは分ける必要がある。

# 作業内容

- progress/project-master/00017-00-assess-provider-loading-policy-and-harmonize-docs.md、README、architecture docs、provider docs、provider profile、runner、Ollama/OpenAI-compatible client と adapter を確認した。
- Ollama API docs で keep_alive が duration または 0、response に load_duration が含まれることを確認した。
- LM Studio 公式 docs で、JIT loading default enabled、JIT loaded model の Idle TTL default 60 minutes、Auto-Evict default enabled、API request で ttl を指定可能、lms load はデフォルト TTL なし、non-JIT loaded model は Auto-Evict 対象外であることを確認した。

# 判断

## 横断解釈

- Ollama も LM Studio も動的ロードに近いが、運用政策は同じではない。
- Ollama の現構成は benchmark 側が keep_alive を毎 request に渡し、常駐時間を短く延長する client-driven policy である。
- LM Studio の既定は server 側の JIT loading、Idle TTL、Auto-Evict でロードと退避を扱う server-driven policy であり、現行 client はその既定値を利用するだけで、ttl や専用 load API には関与しない。
- 現在の LM Studio alias 手動 load は、この server-driven default への一般推奨ではなく、readiness 用に API 参照名を固定するための明示的な例外として読むべきである。

## 1. Ollama keep_alive = 5m の位置づけ

- keep_alive = 5m は、同一 model に対して複数 prompt を短時間に連続実行する用途では妥当である。現行 runner は model ごとに prompt 群をまとめて回すため、同一 model block 内の再ロードを減らしやすい。
- ただし runner は並列実行しないので、5m が改善するのは同時実行数ではなく、同一 model を短い間隔で呼ぶときの再ロード回避だけである。
- 問題化するのは、1 model あたりの prompt 束が短いのに model 数が多い run、VRAM や RAM が厳しい環境、大きい model を順に切り替える run、ほかの local app と GPU を共有する運用である。この場合、前の model が最後の request 後も約 5 分残り、次の model と常駐が重なりやすい。
- readiness や smoke のように 1 model あたり 1 ないし数 request しか打たない用途では、5m は保守的というより常駐寄りであり、メリットよりメモリ滞留の説明責務が大きい。
- 結論として、configs/provider_profiles/local-default.toml の keep_alive = 5m は baseline 向け既定値としては維持可能だが、低メモリ環境や多 model 運用の一般推奨値としては読ませない方がよい。docs では latency 寄り default と明示し、必要に応じて 0 または短い duration に下げる運用を案内するべきである。

## 2. LM Studio の alias 手動 load 前提の位置づけ

- lms load --identifier による alias 固定は、readiness 文脈では有効である。実際の downloaded model key を docs と config から切り離し、利用者に同じ API-visible 名を要求できるためである。
- ただしこれは LM Studio の一般推奨ロード政策とは言いにくい。理由は 2 つある。1 つ目は、LM Studio の既定は JIT loading default enabled であり、他アプリからの最初の request で自動 load される点である。2 つ目は、lms load の default には TTL がなく、non-JIT loaded model は Auto-Evict 対象外なので、明示 load を一般化すると手動 unload 前提の pin 運用になりやすい点である。
- 現行の llmb-minimal-chat alias は、openai-compatible-minimal-v1 の readiness slot としては妥当である。一方で、LM Studio を使った正式比較や multi-model benchmark の標準形としては推奨しない方がよい。
- 一般運用の読み方としては、LM Studio は server-managed dynamic loading を前提に読み、将来 multi-model 比較を追加するなら actual model identifier を config に持たせて JIT と Auto-Evict を使う方が素直である。
- 結論として、alias 手動 load 前提は readiness 用に限定し、docs 上でもその位置づけを明記するべきである。

## 3. 今やるべき変更範囲

- 今回の request は code 追加を正当化しない。provider-specific unload hook、LM Studio 固有 load/unload API の追加、OpenAI-compatible payload への ttl 送信、preflight endpoint 呼び出しは不要である。
- 現在の config 分離は大筋で妥当である。Ollama baseline は local-default.toml、OpenAI-compatible readiness は openai-compatible-local.toml と openai-compatible-minimal-v1 に閉じており、今すぐ config schema や source code を変える必要はない。
- 必要なのは docs 側の政策明文化である。benchmark core は model の download、load、pin、unload を自動化しないこと、Ollama は client-driven residency、LM Studio は server-driven dynamic loading が default であること、現行 alias slot は readiness 専用であることを明示すべきである。
- したがって、今やるべき変更は docs 中心で足りる。config は意図の説明対象ではあるが、ファイル内容の必須変更までは不要である。

## 4. provider docs の統一方針

- 揃えるべきなのはページ数ではなく責務境界である。
- 各 provider directory の README は landing page 兼 index とし、詳細手順の本体にはしない。
- provider README の共通見出しは次で揃える。
  - provider の位置づけ
  - ロード政策の要約
  - readiness と benchmark の読み分け
  - 最短確認
  - 詳細ページ
  - 公式参照先
- 実行コマンド主体の詳細は、変更理由ごとに subpage へ分ける。install/setup、api-check または loading-readiness、必要なら benchmark-operation、の粒度で十分である。
- 現在の Ollama docs は index 役と subpage 分離ができているので、その役割を維持しつつ keep_alive の意味を補足すればよい。
- LM Studio docs は README が単独手順書になっているため、README を landing page 化し、現在のコマンド中心手順は新しい詳細ページへ移す方が統一しやすい。最小案としては docs/lmstudio/api-check.md か docs/lmstudio/loading-and-readiness.md を追加し、README からリンクする。
- root README は provider 非依存の最小方針だけを残し、個別の load policy 詳細は provider docs に逃がす。docs/architecture/benchmark-foundation.md は cross-provider policy のみを持つ。

## 5. 今 docs に明記すべきこと

- runner は逐次実行であり、現行 benchmark に provider-aware parallel scheduler はない。
- benchmark core は model を自動 download、load、pin、unload しない。
- Ollama では provider profile の keep_alive を毎 request に渡している。
- LM Studio では default で JIT loading が有効で、JIT loaded model の Idle TTL は default 60 minutes、Auto-Evict は default enabled である。
- 現行 OpenAI-compatible client は ttl を送らないので、LM Studio の JIT path を使う場合は server 側 default policy をそのまま使う。
- llmb-minimal-chat alias と openai-compatible-minimal-v1 は readiness 用であり、正式比較用 suite ではない。
- Ollama では response に load_duration が含まれるため、reload cost の観測は code 追加なしで行える。

## 6. 今回 defer すべきこと

- provider-specific unload hook の追加
- LM Studio 固有の load/unload endpoint や preflight endpoint の統合
- OpenAI-compatible payload への ttl 送信
- cross-provider 共通の loading_policy config schema 追加
- LM Studio 向け正式 multi-model comparison suite の設計
- load_duration を使った自動 keep_alive tuning
- runner の並列実行や provider-aware scheduling

# 成果

- Ollama は client-driven residency、LM Studio は server-driven dynamic loading という読み分けを確定した。
- Ollama keep_alive = 5m は baseline 向け既定値としては維持可能だが、低メモリや多 model 運用の一般推奨ではないと整理した。
- LM Studio の alias 手動 load は general recommendation ではなく readiness 専用 slot として限定すべきと判断した。
- 今回は docs 更新だけで足り、config schema や source code の追加変更は不要と結論づけた。
- provider docs は README を landing page、詳細手順を subpage に分ける方針で統一する設計を固めた。

# 設計対象

- Ollama と LM Studio のロード政策の読み分け
- readiness 専用構成と正式 benchmark 構成の境界
- provider docs、README、architecture doc の責務分担

# 設計判断

- Ollama の keep_alive = 5m は baseline default としては許容し、docs で low-memory override を明示する。
- LM Studio の alias 手動 load は openai-compatible-minimal-v1 の readiness 運用に限定する。
- benchmark core は load/unload に踏み込まず、provider docs で政策差を説明する。
- docs 構成は provider README を index 化し、詳細手順は subpage 化して揃える。

# 影響範囲

- README.md
- docs/architecture/benchmark-foundation.md
- docs/ollama/README.md
- docs/ollama/api-check.md
- docs/lmstudio/README.md
- 必要なら docs/lmstudio 配下の新規詳細ページ 1 枚

# リスク

- LM Studio の alias 手動 load を一般推奨のように残すと、将来の multi-model benchmark docs が pin 運用前提に引きずられる。
- Ollama keep_alive の意味を書かないままだと、低メモリ環境での常駐や reload の問題が benchmark 自体の不具合に見えやすい。
- provider README の役割が揃わないままだと、README、architecture、provider docs のどこに何を書くかが再び崩れる。

# 改善提案

- 後続 request では、Ollama の low-memory 例として keep_alive = 0 または短時間の override 例を docs に追加すると運用判断がしやすい。
- LM Studio を正式比較へ広げる段階で、actual backing model 名を config や run metadata へ明示する方針を別 request で整理するとよい。
- 比較用途が増えたら、load_duration や backing model identity を report surface に載せる検討余地がある。

# 次アクション

- programmer は docs のみを更新対象とし、source code と config schema は変えない。
- programmer への具体指示は次のとおり。
  1. docs/ollama/README.md に「ロード政策の要約」と「readiness と benchmark の読み分け」を追加し、local-default.toml の keep_alive = 5m が latency 寄り default であること、低メモリ時は短くするか 0 にできることを明記する。
  2. docs/ollama/api-check.md に、sample CLI 経路では keep_alive = 5m を送ることと、response の load_duration が reload cost の観測点になることを短く追記する。
  3. docs/lmstudio/README.md は landing page へ作り替え、JIT default policy と readiness 用 explicit alias load を分けて説明する。README 自体は index 役に留める。
  4. docs/lmstudio 配下に詳細手順ページを 1 枚追加し、現在の lms get -> lms server start -> lms load --identifier llmb-minimal-chat -> /v1/models -> benchmark 実行、の流れを移す。そのページでは readiness 用導線であることを明記する。ページ名は api-check.md か loading-and-readiness.md を推奨する。
  5. README.md には provider 非依存の短い追記だけを行い、benchmark core は model の自動 load/unload をしないこと、Ollama は keep_alive、LM Studio は JIT default で読むこと、llmb-minimal-chat alias は readiness 用であることを 2 から 4 文で整理する。
  6. docs/architecture/benchmark-foundation.md には cross-provider loading policy を短く追記し、core は provider 非依存、runner は逐次実行、load/unload は provider 運用に委ねることを明記する。
  7. configs/provider_profiles/local-default.toml、configs/provider_profiles/openai-compatible-local.toml、src/local_llm_benchmark/providers/ollama/client.py、src/local_llm_benchmark/providers/openai_compatible/client.py は今回変更しない。docs で意図だけを補足する。
