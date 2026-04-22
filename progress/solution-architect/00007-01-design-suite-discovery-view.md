---
request_id: "00007"
task_id: "00007-01"
parent_task_id: "00007-00"
owner: "solution-architect"
title: "design-suite-discovery-view"
status: "done"
depends_on: []
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-18T10:30:00+09:00"
related_paths:
  - "README.md"
  - "configs"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/config"
  - "src/local_llm_benchmark/registry/model_registry.py"
  - "src/local_llm_benchmark/prompts/repository.py"
---

# 入力要件

- 利用可能な benchmark suite と、各 suite で必要な provider / model が分かる導線を設計したい。

# 整理した要件

- information overload を避けつつ、共有された config から「何ができるか」と「何を準備するか」が分かること。
- provider 固有コマンド例を共通 CLI に持ち込まず、config から解決できる provider_id と model identifier を中心に見せること。
- 一覧と詳細の導線は短く保ち、README を読まなくても次の実行操作へ進めること。

# 作業内容

- README、既存 CLI、config loader / models、model registry、prompt repository、sample config、親 task を確認し、現状は `run` のみで suite discovery 導線が欠けていることを整理した。
- benchmark suite から機械的に引ける情報として、suite_id、description、tags、model selector、resolved model 一覧、provider_id、provider_model_name、prompt set、resolved prompt 数、prompt category が使えることを確認した。
- 情報過多を避けるため、一覧は短い要約、詳細は provider / model と prompt 構成に絞る 2 段階表示が妥当と判断した。

# 判断

- 推奨 CLI 形状は、トップレベルに `suites` を 1 つ追加し、同一コマンド内で 2 段階に振る舞わせる形とする。
- 一覧は `local-llm-benchmark suites --config-root configs`、詳細は `local-llm-benchmark suites <suite_id> --config-root configs` を推奨する。`run` が既に `--suite` を使っているため、discovery 側は positional の方が短く、一覧と詳細の切り替えが分かりやすい。
- 一覧表示の最小項目は `suite_id`、短い description、解決後の model 数、解決後の prompt 数、参照 provider_id 要約とする。generation 設定や raw selector 条件は一覧には出さない。
- suite 指定時の詳細表示では、description、tags、prompt set / category 要約、準備すべき provider_id と provider_model_name 一覧、実行用の次アクションだけを出す。model default generation や provider profile の接続設定は discovery の主目的から外れるため省く。
- 「準備するもの」は provider 固有の取得コマンドではなく、「この suite が参照する provider_id」と「その provider 上で利用可能にしておく model identifier」を grouped 表示する。これなら provider 非依存のまま準備対象が伝わる。
- 実装は config schema を増やさず、`load_config_bundle`、`InMemoryModelRegistry`、`InMemoryPromptRepository` を再利用して解決済み view を組み立てる方針が最小である。

# 成果

## 推奨 CLI 形状

- 追加するサブコマンド名は `suites` を推奨する。
- 1 つのサブコマンドで十分だが、利用体験は「一覧」と「詳細」の 2 段階にする。
- 想定コマンドは次の 2 つとする。

```text
local-llm-benchmark suites --config-root configs
local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs
```

- 理由は次の通り。
  - `suite` という対象名がそのままコマンド名になり、README の文脈と一致する。
  - nested subcommand の `list` / `show` を増やさずに済み、help 面が肥大化しない。
  - 詳細だけ必要なときも 1 語追加で到達できる。

## 表示例の草案

一覧表示の草案:

```text
利用可能な suite: 1

- local-three-tier-baseline-v1
  3 ランク各 1 モデルで比較する初期 baseline
  3 モデル / 3 プロンプト / provider: ollama

次の操作: 詳細は `local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs`
準備できたら: `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1`
```

詳細表示の草案:

```text
suite: local-three-tier-baseline-v1
概要: 3 ランク各 1 モデルで比較する初期 baseline
tags: baseline, three-tier

評価対象
- prompt set: core-small-model-ja-v1
- resolved prompts: 3
- categories: classification, extraction, rewrite

準備するもの
- provider: ollama
- models:
  - local.entry.gemma3 -> gemma3:latest
  - local.balanced.qwen2_5 -> qwen2.5:7b
  - local.quality.llama3_1 -> llama3.1:8b

次の操作
- provider 側で上記 model identifier を利用可能にする
- local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1
```

表示仕様の要点:

- 一覧は 1 suite あたり 3 行までを目安にし、terminal 幅に収まりやすい短い要約に留める。
- 詳細は「評価対象」「準備するもの」「次の操作」の 3 ブロックに固定し、利用開始に必要な情報だけに絞る。
- 複数 provider がある suite では `provider_id` ごとに model を group して表示する。
- 表示順は suite_id、provider_id、model_key、prompt category を安定ソートし、テストしやすくする。

## 最小実装方針

- `src/local_llm_benchmark/cli/main.py`
  - `suites` サブコマンドを追加する。
  - handler は config 読込と view モジュール呼び出しだけに留める。
- `src/local_llm_benchmark/cli/suite_catalog.py` を新設する。
  - ConfigBundle から一覧 / 詳細の表示用データを組み立てる。
  - `InMemoryModelRegistry.resolve_selector()` と `InMemoryPromptRepository.resolve_prompt_set_ids()` を使って解決済み件数と provider / model 一覧を得る。
  - テキスト整形もこのモジュールに閉じ込め、main.py は薄く保つ。
- `src/local_llm_benchmark/config` の schema は変更しない。
- テストは `tests/cli` に追加し、一覧表示、詳細表示、存在しない suite 指定時の案内、複数 provider を想定した並び順を確認する。

## 懸念点

- 現行 config の `description` には `task_id` 接頭辞を含むものがあり、そのまま出すと一覧がやや内部向けに見える。v1 では description をそのまま使い、必要なら後続で user-facing な `summary` フィールド追加を検討する。
- tag ベース selector の suite が増えると、解決後 model 数が環境ごとの差分ではなく config bundle 差分に依存するため、詳細では「解決結果」を正本として表示する必要がある。
- provider が多い suite では詳細出力が縦に伸びるため、prompt ごとの個別 ID や generation 設定まで表示すると情報過多になりやすい。

# 次アクション

- programmer が `suites` サブコマンドと表示モジュールを追加し、一覧 / 詳細 / エラー時の CLI テストを実装する。
- reviewer が provider 固有の取得コマンド例が共通層に入っていないか、一覧が過密になっていないかを確認する。

# 関連パス

- README.md
- configs
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/config

# 設計対象

- benchmark suite の discovery 導線として自然な CLI 形状。
- 一覧と詳細で分けるべき表示情報の境界。
- provider 非依存のまま準備対象を伝える表示表現。
- 実装時に既存責務を崩さない最小追加モジュール境界。

# 設計判断

- コマンド面は `suites` の 1 サブコマンドに統一し、引数の有無で list / detail を切り替える。
- 一覧は選択のための導線、詳細は準備と実行のための導線と割り切る。
- 詳細で見せる provider / model は selector 条件そのものではなく、config bundle から解決した結果を正本とする。
- README へ戻らなくても run まで進めるよう、最後に短い 1 行案内を必ず出す。
- provider 側の CLI 名や取得方法は表示しない。共通層で出すのは provider_id と model identifier までに留める。

# 影響範囲

- `src/local_llm_benchmark/cli/main.py` の parser と handler 追加。
- 新設する `src/local_llm_benchmark/cli/suite_catalog.py` の view 組み立てと text renderer。
- `tests/cli` の snapshot 相当テスト、並び順テスト、unknown suite テスト。
- 実装後は README の最小利用導線に `suites` の 1 行追加が妥当。

# リスク

- description が内部向け文言のままだと、CLI の user-friendly さが config 記述品質に引きずられる。
- loader 側の validation と suite_catalog 側の解決ロジックが二重化すると、将来の selector 追加時に表示と実行がずれる恐れがある。
- 将来 prompt set が大きくなったときに prompt title まで出し始めると、terminal 表示がすぐに過密になる。

# 改善提案

- 実装初回は text 出力に限定し、機械向け出力の `--format json` は要求が出た時点で追加する。
- suite の説明文が内部向けになりやすい場合は、後続 request で `description` とは別に短い `summary` を benchmark suite schema へ追加する。
- selector 解決ロジックが CLI 以外でも必要になったら、その時点で `config` 配下へ共通 resolver を抽出し、初回から過分割しない。