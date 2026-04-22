# TASK-00011-01 prompt 仕様確定

- Status: done
- Role: solution-architect
- Parent: TASK-00011
- Related IDs: REQ-00001, FUN-00101, FUN-00207, FUN-00308, CFG-00101, CFG-00102, CFG-00104, CFG-00107, CFG-00108, CFG-00201, CFG-00204, CFG-00206, CFG-00207, PVD-00401, OOS-00001, NFR-00303, NFR-00402
- 起票日: 2026-04-22

## 目的

TASK-00011 で追加する `.github/prompts/` 群について、ヒアリング項目、出力形式、参照情報源、
既存 sample config との関係を先に確定し、docs-writer が迷わず prompt 本体を執筆できる状態にする。

## 設計対象

- 対象 prompt は v1.1.0 で追加する 2 本のみとする。
  - コンフィグ生成 prompt
  - model-recommender prompt
- 診断レポート prompt は TASK-00011 のスコープ外とし、既存 `report` 出力と v2.0.0 Web UI 側へ寄せる。
- 現行 trunk を正本とし、`.github/prompts/` は新設前提、`tmp/v0.1.0/` は参照しない。

## 完了条件

- コンフィグ生成 prompt について以下が確定している:
  - TaskProfile / Provider / Run / Comparison を 4 ファイル個別生成すること
  - 出力先フォルダを askQuestions で必ず確認し、sample config 上書きを避ける導線を持つこと
  - 既存 sample config (`configs/`) を参照例としてどう案内するか
- model-recommender prompt について以下が確定している:
  - provider を先にヒアリングすること
  - Web 情報の優先順位 (一次情報優先 / 補助情報の扱い) と提示フォーマット
  - PC スペック / 用途 / 制約から推薦理由をどう組み立てるか
- 診断レポート prompt を v1.1.0 に残すか、v2.0.0 の Web UI 側へ寄せるかが結論づけられている
- `.github/prompts/` 配下のファイル分割方針と各 prompt の役割一覧がまとまっている

## スコープ外

- `.github/prompts/` 本体の執筆 (TASK-00011-02)
- prompt の最終レビュー (TASK-00011-03)
- 新規 CLI 実装

## 設計判断

### 1. 2 prompt の責務境界

#### 1-1. コンフィグ生成 prompt

- 役割:
  - 1 回の起動で 4 種別のうち 1 ファイルだけを生成する。
  - 生成対象は TaskProfile / Provider / Run / Comparison の 4 TOML に限定する。
  - 出力先フォルダを必ずヒアリングし、既存 sample config を参照専用として扱う。
- 含める責務:
  - 必須ヒアリングの実施
  - 現行 repo の sample config 形状に沿った TOML ひな形の生成
  - sample config を上書きしないガード
- 含めない責務:
  - モデル推薦
  - 診断レポート生成
  - `model_candidates.toml` の生成
- 補足:
  - 現行 trunk では Run 設定が `model_candidate` を参照するため、Run 生成時は既存 `model_candidates.toml` に登録済みの名前を必須入力にする。
  - `model_candidates.toml` が未整備の場合、prompt は新規生成へ拡張せず、sample を参照して手動で整備するよう案内する。

#### 1-2. model-recommender prompt

- 役割:
  - provider を先にヒアリングし、その provider で利用可能なモデル候補を Web 情報から収集して提示する。
  - PC スペック / 用途 / 制約から候補比較と推奨理由を返す。
- 含める責務:
  - provider 先行ヒアリング
  - 一次情報優先の情報収集
  - 候補比較、特徴整理、推奨理由の提示
- 含めない責務:
  - config ファイル生成
  - 実測診断や既存結果の分析
- 補足:
  - 現行 trunk の benchmark 実行対象 provider は Ollama のみであるため、他 provider を選んだ場合は「推薦は advisory、現行 CLI 実行整合は未保証」と明示する。

### 2. `.github/prompts/` 配下のファイル分割と推奨ファイル名

- VS Code 公式の prompt file 仕様に合わせ、workspace 配置は `.github/prompts/`、拡張子は `.prompt.md` とする。
- v1.1.0 では以下 2 ファイルに分割する。
  - `.github/prompts/config-generator.prompt.md`
  - `.github/prompts/model-recommender.prompt.md`
- docs-writer は各 prompt に少なくとも以下を持たせる。
  - frontmatter: `name`, `description`, `argument-hint`
  - 本文: 目的、前提、必須ヒアリング、分岐規則、出力フォーマット、スコープ外
- ヒアリングの実装手段は prompt file の入力変数または `vscode/askQuestion` 相当の仕組みとし、本文仕様上は「必須項目を対話で回収すること」を要件とする。

### 3. コンフィグ生成 prompt の askQuestions 項目一覧

#### 3-1. 全生成種別で共通の必須項目

- どの設定ファイルを生成するか
  - `task-profile`
  - `provider`
  - `run`
  - `comparison`
- 出力先フォルダの絶対またはワークスペース相対パス
- 生成ファイル名
- 出力先が sample config 配下ではないことの確認

#### 3-2. TaskProfile 生成時の必須項目

- TaskProfile 名
- 用途カテゴリまたは purpose
- 説明の有無
- scorer 名
- scorer 引数の有無
- case 件数 (1 件以上)
- 各 case の `name`
- 各 case の `input`
- 各 case の `expected_output`

#### 3-3. Provider 生成時の必須項目

- provider kind
  - v1.1.0 では `ollama` のみを正規生成対象とする
- host
  - 既定は `localhost`
- port
  - 既定は `11434`
- timeout_seconds

#### 3-4. Run 生成時の必須項目

- 既存 `model_candidates.toml` に登録済みの `model_candidate` 名
- 実行対象 `task_profiles` 名の配列
- `n_trials` (1 以上)
- 生成条件を TOML に含めるか
- 含める場合の `temperature`
- 含める場合の `seed`
- 含める場合の `max_tokens`
- `store_root` を TOML に含めるか

#### 3-5. Comparison 生成時の必須項目

- 比較対象 Run 数の想定
  - 最小 2
  - 実行前生成では実 Run ID の代わりに placeholder を入れる
- `ranking_axis_default`
  - `quality`
  - `speed`
  - `integrated`
- `integrated` を使う場合の `w_quality`
- `integrated` を使う場合の `w_speed`
- `store_root` を TOML に含めるか

### 4. コンフィグ生成 prompt が出力する 4 TOML の最小項目

#### 4-1. TaskProfile TOML

- 出力先:
  - ユーザー指定フォルダ配下の `task_profiles/<name>.toml`
- 最小項目:
  - `[task_profile].name`
  - `[task_profile].purpose`
  - `[task_profile.scorer].name`
  - `[task_profile.scorer].args`
  - `[[task_profile.cases]].name`
  - `[[task_profile.cases]].input`
  - `[[task_profile.cases]].expected_output`
- sample との関係:
  - `configs/task_profiles/qa-basic.toml` を構造参照元とする
  - sample ファイル自体は編集・上書きしない

#### 4-2. Provider TOML

- 出力先:
  - ユーザー指定フォルダ配下の `providers.toml`
- 最小項目:
  - `[[provider]].kind`
  - `[[provider]].host`
  - `[[provider]].port`
  - `[[provider]].timeout_seconds`
- sample との関係:
  - `configs/providers.toml` を構造参照元とする
  - v1.1.0 で benchmark 実行整合を持つ kind は `ollama` のみ

#### 4-3. Run TOML

- 出力先:
  - ユーザー指定フォルダ配下の `run.toml`
- 最小項目:
  - `[run].model_candidate`
  - `[run].task_profiles`
  - `[run].n_trials`
- 条件付きで含める項目:
  - `[run].store_root`
  - `[run.generation].temperature`
  - `[run.generation].seed`
  - `[run.generation].max_tokens`
- sample との関係:
  - `configs/run.toml` を構造参照元とする
  - ただし `model_candidate` は別管理の `model_candidates.toml` を参照するため、prompt は sample `configs/model_candidates.toml` を参照案内のみ行う
  - `model_candidates.toml` は本 prompt の生成対象外

#### 4-4. Comparison TOML

- 出力先:
  - ユーザー指定フォルダ配下の `comparison.toml`
- 最小項目:
  - `[comparison].runs`
- テンプレートとして既定で含める項目:
  - `[comparison].ranking_axis_default`
  - `[comparison].store_root`
  - `[comparison.weights].w_quality`
  - `[comparison.weights].w_speed`
- sample との関係:
  - `configs/comparison.toml` を構造参照元とする
  - 実 Run 前に生成する場合は `REPLACE_WITH_RUN_ID_A` / `REPLACE_WITH_RUN_ID_B` 形式の placeholder を入れたテンプレートとして返す
  - prompt は placeholder が残る限り compare 実行前に置換が必要であることを明記する

### 5. sample config との関係と上書き防止

- `configs/` 配下は現行 trunk の read-only sample として扱う。
- prompt は sample の構造・既定値例を参照してよいが、出力先には使わない。
- 出力先フォルダは必須ヒアリングとし、以下を禁止する。
  - `configs/` 直下への新規生成
  - `configs/task_profiles/qa-basic.toml` の上書き
  - `configs/providers.toml` の上書き
  - `configs/run.toml` の上書き
  - `configs/comparison.toml` の上書き
- ユーザーが sample と同名ファイルを sample 配下に出したいと答えた場合、prompt は別フォルダを再ヒアリングする。

### 6. model-recommender prompt の askQuestions 項目一覧

- provider 名
  - 最初に必ず聞く
- 利用 OS
- CPU 名またはクラス
- メモリ容量
- GPU 有無
- GPU 名と VRAM 容量
- 主用途
  - 例: 要約 / 分類 / 短文 QA / コーディング補助 / 翻訳
- 入出力の主言語
- 品質重視か速度重視か
- 許容できる最大モデル規模またはメモリ制約
- 応答長の傾向
  - 短文中心か長文中心か
- ライセンスやオフライン運用などの追加制約
- 候補を何件提示してほしいか

### 7. model-recommender prompt の情報源方針

- 原則:
  - provider ごとの公式情報を最優先する
  - 公式情報で不足する属性のみ、補助情報で補完する
- 一次情報の優先順:
  - 対象 provider の公式モデル一覧・公式ドキュメント・公式 API/ライブラリ掲載情報
  - 各モデルの公式 model card、メンテナ repository、ベンダー公式配布ページ
- 補助情報の利用条件:
  - 公式情報だけで候補比較に必要な属性が足りない場合のみ使用する
  - 使用時は「補助情報」であることを回答中に区別する
- 回答で必ず明示する項目:
  - provider 上での利用可否の根拠
  - ハードウェア適合の根拠
  - 主用途との適合理由
  - 採用しなかった候補の主な理由
- Web アクセス不可時のフォールバック:
  - Web 参照できないことを明示する
  - provider 上の候補モデル一覧または候補名をユーザーに貼ってもらう
  - ユーザー提供情報と一般的なハードウェア目安だけで暫定推薦を返す
  - provider 上で利用可能と断定できない情報は推測で補わない

### 8. model-recommender prompt の返答形式

- 返答は少なくとも以下の順で構成する。
  - ヒアリング要約
  - 候補一覧
  - 推奨順位
  - 各候補の特徴
  - 最終推奨理由
  - 現行 repo スコープとの整合注記
- 候補一覧では少なくとも以下を並べる。
  - モデル名
  - provider 上の識別子または掲載名
  - 想定リソース感
  - 強み
  - 注意点
  - 推薦理由
- 必要に応じて最後に「benchmark 実行に進むなら config-generator prompt と `model_candidates.toml` 整備が必要」と案内してよいが、config 自体は生成しない。

## 影響範囲

- TASK-00011-02 docs-writer:
  - 上記 2 ファイル名、責務境界、必須ヒアリング、回答フォーマットに従って prompt 本体を執筆する
- TASK-00011-03 reviewer:
  - 2 prompt だけであること
  - config-generator が 4 TOML 個別生成であること
  - model-recommender が provider 先行ヒアリングであること
  - Web 不可時フォールバックと sample 上書き防止が明記されていること
- 既存 repo 正本との整合:
  - `README.md` の v1.1.0 記述
  - `configs/` 配下の sample 形状
  - `tests/test_config.py` と `tests/test_comparison_config.py` が示す最小構成

## 残課題

- docs-writer が `.github/prompts/` 本体を執筆する
- reviewer が prompt 本体の文面と実際の対話導線を確認する
- `model_candidates.toml` を prompt スコープ外に据えた判断が v1.1.0 の利用者導線として十分かは、prompt 本体レビュー時に再確認する

## 進捗ログ

- 2026-04-22 project-master: 子 task 起票。現行 trunk には `.github/prompts/` と `configs/model_registry/` が存在しないため、現実のリポジトリ構成に合わせて prompt 仕様を再定義する必要あり
- 2026-04-22 solution-architect: Status を `in-progress` として着手。`README.md`、`configs/README.md`、`configs/task_profiles/qa-basic.toml`、`configs/model_candidates.toml`、`configs/providers.toml`、`configs/run.toml`、`configs/comparison.toml`、`tests/test_config.py`、`tests/test_comparison_config.py`、`docs/design/06-configuration-sources.md`、`docs/design/07-provider-contract.md` を確認し、現行 trunk の正本を基準に prompt 仕様を確定した。
- 2026-04-22 solution-architect: 仕様を 2 prompt に確定。config-generator は 4 TOML を 1 ファイルずつ生成し、出力先フォルダを必須ヒアリング、sample config は read-only とした。Run 生成時の `model_candidate` 参照整合のため、`model_candidates.toml` は sample 参照のみで prompt 生成対象外と明記した。
- 2026-04-22 solution-architect: model-recommender は provider 先行ヒアリング、公式情報優先、補助情報は不足時のみ、Web 不可時はユーザー貼り付け情報へのフォールバックとした。診断レポート prompt は TASK-00011 スコープ外のままとし、本 task を `done` に更新した。

## レビュー記録 (reviewer 用)

- 未着手