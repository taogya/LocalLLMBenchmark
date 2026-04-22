---
name: config-generator
description: TaskProfile / Provider / Run / Comparison のいずれか 1 ファイルだけを対話で生成する
argument-hint: 生成したい設定種別、出力先フォルダ、用途や制約
---

# 目的

LocalLLMBenchmark 用の設定ファイルを 1 回の起動で 1 ファイルだけ生成する。生成対象は TaskProfile / Provider / Run / Comparison の 4 種別に限る。

# 前提

- 最初に生成対象を 1 つだけ確定してから進める。
- 出力先フォルダは必ず確認する。
- configs/ 配下は read-only sample。参照はしてよいが、新規生成先にしてはいけない。
- 次の sample は構造確認用としてのみ扱う。
  - TaskProfile: configs/task_profiles/qa-basic.toml
  - Provider: configs/providers.toml
  - Run: configs/run.toml
  - Comparison: configs/comparison.toml
  - model_candidate 名の確認: configs/model_candidates.toml
- model_candidates.toml はこの prompt の生成対象外。Run を作るときは、既存 model_candidates.toml に登録済みの model_candidate 名を入力させる。

# 必須ヒアリング

不足があるまま生成しない。まず共通項目を聞き、その後に生成対象ごとの項目を聞く。

## 共通

- 生成対象: task-profile / provider / run / comparison
- 出力先フォルダ: 絶対パスまたはワークスペース相対パス
- 生成ファイル名
- 出力先が configs/ 配下ではないことの確認

## TaskProfile

askQuestions:
- TaskProfile 名
- purpose
- description を入れるか
- scorer 名
- scorer args を入れるか
- case 件数
- 各 case の name
- 各 case の input
- 各 case の expected_output

出力 TOML の最小項目:
- [task_profile].name
- [task_profile].purpose
- [task_profile.scorer].name
- [task_profile.scorer].args
- [[task_profile.cases]].name
- [[task_profile.cases]].input
- [[task_profile.cases]].expected_output

出力先の既定形:
- <出力先フォルダ>/task_profiles/<TaskProfile 名>.toml

## Provider

askQuestions:
- provider kind
- host
- port
- timeout_seconds

出力 TOML の最小項目:
- [[provider]].kind
- [[provider]].host
- [[provider]].port
- [[provider]].timeout_seconds

出力先の既定形:
- 出力先フォルダ配下の providers.toml

補足:
- v1.1.0 で benchmark 実行整合がある provider kind は ollama のみ。ほかの kind を指定されたら、通常生成対象外であることを伝え、ollama に切り替えるか確認する。

## Run

askQuestions:
- 既存 model_candidates.toml に登録済みの model_candidate 名
- task_profiles 配列
- n_trials
- generation を含めるか
- generation を含める場合の temperature
- generation を含める場合の seed
- generation を含める場合の max_tokens
- store_root を含めるか
- store_root を含める場合の値

出力 TOML の最小項目:
- [run].model_candidate
- [run].task_profiles
- [run].n_trials

条件付きで含める項目:
- [run].store_root
- [run.generation].temperature
- [run.generation].seed
- [run.generation].max_tokens

出力先の既定形:
- 出力先フォルダ配下の run.toml

補足:
- model_candidate は既存名のみ受け付ける。未登録名の新規作成には進まない。
- 登録名が不明な場合は、configs/model_candidates.toml を構造例として案内し、利用者に既存名を確認してもらう。

## Comparison

askQuestions:
- 比較対象 Run 数
- runs に入れる値
- ranking_axis_default
- integrated を使う場合の w_quality
- integrated を使う場合の w_speed
- store_root を含めるか
- store_root を含める場合の値

出力 TOML の最小項目:
- [comparison].runs

条件付きまたは推奨で含める項目:
- [comparison].ranking_axis_default
- [comparison].store_root
- [comparison.weights].w_quality
- [comparison.weights].w_speed

出力先の既定形:
- 出力先フォルダ配下の comparison.toml

補足:
- runs は 2 件以上を前提にする。
- 実 Run 前に作る場合は REPLACE_WITH_RUN_ID_A / REPLACE_WITH_RUN_ID_B のような placeholder を使ってよい。
- placeholder が残っている限り compare 実行前に置換が必要と明記する。

# 分岐規則

- 生成対象が未確定なら、ほかの質問より先に生成対象を確定する。
- 出力先フォルダが configs/ 配下、または sample と同名ファイルの上書きになる場合は拒否し、別フォルダを再ヒアリングする。
- 1 回の応答で複数ファイルを生成しない。複数必要なら、次回起動で別ファイルを生成するよう案内する。
- Run 生成で model_candidate 名が未確定なら生成を止め、既存 model_candidates.toml の登録名入力を求める。
- Comparison 生成で runs が 2 件未満なら、2 件以上になるまで再ヒアリングする。
- ranking_axis_default が integrated なら weights を必須にする。integrated 以外なら weights は省略可能と伝える。

# 出力フォーマット

不足情報がある場合は、まず不足分だけを質問し、TOML をまだ出さない。情報がそろったら次の順で返す。

1. 生成対象
2. 出力先パス
3. 注意点
4. 生成結果

生成結果では次を守る。

- 返す TOML は 1 ファイル分だけにする。
- TOML は ```toml のコードブロックで返す。
- sample を上書きしないことを 1 行で再確認する。
- Comparison の placeholder や Run の model_candidate など、実行前に確認が要る点だけを短く補足する。

# スコープ外

- model_candidates.toml の生成や更新
- モデル推薦
- 複数ファイルの一括生成
- benchmark 実行や結果診断
- configs/ 配下の sample 編集