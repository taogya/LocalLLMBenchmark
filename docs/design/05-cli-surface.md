# 05. CLI 表面 (CLI Surface)

ユーザーが直接触る CLI を、サブコマンド単位で概念定義します。実装ライブラリ (argparse / click 等) や内部関数名には踏み込みません。本書はサブコマンド名、責務、入出力境界、終了状態の分類を定めます。

関連既存 ID: REQ-00001, REQ-00002, FUN-00104, FUN-00207, FUN-00307, FUN-00308, FUN-00309, FUN-00310, FUN-00305, FUN-00401, FUN-00402, FUN-00403, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408, FUN-00409, FUN-00410, NFR-00002, NFR-00003, NFR-00004, NFR-00301, NFR-00302, NFR-00501, ARCH-00101, ARCH-00205, ARCH-00206, COMP-00001, COMP-00010, COMP-00011, COMP-00012, FLW-00002〜00012

## 設計原則

| ID | 原則 |
| --- | --- |
| CLI-00001 | 主要操作 (登録確認・実行・結果確認) は単一 CLI から到達可能とする (NFR-00002) |
| CLI-00002 | 1 サブコマンドは 1 つの FLW- に対応する。サブコマンドが複数フローを兼ねない |
| CLI-00003 | 出力は機械可読を一次、人間可読を派生形とする (ARCH-00003) |
| CLI-00004 | 終了コードと標準ストリームは「処理結果がスクリプトから判定可能」となる粒度を保つ |

## サブコマンド一覧

サブコマンドは次の名前と責務で提供します。

| ID | サブコマンド | 対応 FUN- | 対応 FLW- | 対応 COMP- |
| --- | --- | --- | --- | --- |
| CLI-00101 | (superseded by CLI-00106) run | FUN-00201, FUN-00202, FUN-00203, FUN-00206 | FLW-00001 | COMP-00001 → COMP-00003 |
| CLI-00102 | report | FUN-00307, FUN-00302, FUN-00303, FUN-00305 | FLW-00002 | COMP-00001 → COMP-00012 / COMP-00009 |
| CLI-00103 | list (Task Profile / Model Candidate 一覧) | FUN-00104 | (FLW なし) | COMP-00001 → COMP-00007 / COMP-00008 |
| CLI-00104 | runs (過去 Run 一覧) | FUN-00401 | FLW-00004 | COMP-00001 → COMP-00009 |
| CLI-00105 | check (整合性確認) | FUN-00105, FUN-00402 | FLW-00003 | COMP-00001 → COMP-00007 / COMP-00008 |
| CLI-00106 | run (1 Run = 1 Model) | FUN-00207, FUN-00202, FUN-00203, FUN-00206 | FLW-00005 | COMP-00001 → COMP-00010 |
| CLI-00107 | compare | FUN-00308, FUN-00309, FUN-00310, FUN-00305 | FLW-00006 | COMP-00001 → COMP-00011 → COMP-00012 |
| CLI-00108 | comparisons (過去 Comparison 一覧) | FUN-00403 | (FLW なし) | COMP-00001 → COMP-00009 |
| CLI-00109 | system-probe | FUN-00404, FUN-00405 | FLW-00007 | COMP-00001 → COMP-00005 / COMP-00007 |
| CLI-00110 | config lint | FUN-00105, FUN-00402, FUN-00406 | FLW-00008 | COMP-00001 → COMP-00007 / COMP-00008 |
| CLI-00111 | config dry-run | FUN-00407 | FLW-00009 | COMP-00001 → COMP-00007 / COMP-00008 / COMP-00005 |
| CLI-00112 | provider status | FUN-00408 | FLW-00010 | COMP-00001 → COMP-00007 / COMP-00005 |
| CLI-00113 | model pull | FUN-00409 | FLW-00011 | COMP-00001 → COMP-00007 / COMP-00005 |
| CLI-00114 | model warmup | FUN-00410 | FLW-00012 | COMP-00001 → COMP-00007 / COMP-00005 |

## サブコマンドの責務

各サブコマンドの責務は以下に限定します。

### CLI-00101 (superseded by CLI-00106) run

複数 ModelCandidate を同一 Run で扱う代表面として記述していた。1 Run = 1 Model 方針 (FUN-00207) に伴い CLI-00106 で再定義した。

### CLI-00102 report

- ユーザー入力: Run 識別子 / 出力形式
- 出力先: 既定は標準出力。明示指定でファイル出力可能
- ランキングは含まない。モデル横断ランキングは CLI-00107 (compare) で出力する
- 失敗表示: 指定 Run が存在しない場合は「該当なし」を返し、走査結果が空の場合と区別する

### CLI-00103 list

- ユーザー入力: 対象種別 (Task Profile / Model Candidate / 全件)
- 出力先: 標準出力
- 失敗表示: 設定読込時の不整合は CLI-00105 と同じ表現に揃える

### CLI-00104 runs

- ユーザー入力: 絞り込み条件は最小限 (件数上限程度) に留める
- 出力先: 標準出力 (Run 識別子 + 開始時刻 + 対象 Task / Model 概要)

### CLI-00105 check

- ユーザー入力: 設定ソースと静的検証対象 (登録内容 / Comparison 参照)
- 出力先: 検出された問題一覧を標準出力。問題が無い場合も「問題なし」を明示
- 失敗表示: 問題種別ごとに件数を集計し、問題なしなら CLI-00301、問題ありなら CLI-00303 を返す
- 位置づけ: v1.2.0 では既存互換面として維持し、利用者向け主導線は CLI-00110 (`config lint`) を優先する
- 責務境界: provider への通信、host hardware 収集、model 可用性の外部観測は行わない。静的整合性検証に限定する

### CLI-00106 run

- ユーザー入力: 実行対象 (Task Profile 群 / 1 件の Model Candidate / 試行回数 n / 生成条件) を引数または設定参照で指定する。Model Candidate は必ず 1 件
- 出力先: 進捗は標準エラー、Run サマリ (Run 識別子を含む) は標準出力、詳細結果は Result Store のディレクトリ
- 失敗表示: どの Case が、どの失敗種別 (PVD- 参照) で落ちたかを 1 行単位で示す (NFR-00003)
- 複数 Model Candidate を指定してもエラーとし、compare の利用を促す

### CLI-00107 compare

- ユーザー入力: 1 件以上の Run 識別子 (ランキングとして意味が成すのは 2 件以上) / ランキング軸 / 重み上書き / 出力形式
- 出力先: 人間可読 / 機械可読を標準出力またはファイル。Comparison ディレクトリも Result Store に保存される
- 失敗表示: 指定 Run が存在しない、または TaskProfile セットが不一致 (DAT-00109) の場合は Comparison を生成せず該当 Run 識別子と不一致内容を示す

### CLI-00108 comparisons

- ユーザー入力: 絞り込み条件は最小限 (件数上限程度) に留める
- 出力先: 標準出力 (Comparison 識別子 + 作成時刻 + 含まれる Run 識別子概要)

### CLI-00109 system-probe

- ユーザー入力: probe 対象の設定ソース (Provider / Model Candidate)。TaskProfile / Run / Comparison は入力に含めない
- 出力先: 既定は標準出力。JSON を一次出力、Markdown は同一内容の派生表示とする
- 失敗表示: provider unreachable / model unavailable は 1 行 1 件で識別子付きに表示し、probe 自体が完了した場合でも終了コードで判定可能にする (CLI-00307)
- 責務境界: host facts、provider reachability、model availability の観測に限定する。設定静的検証や Run 固有の prompt 組立は含めない

最小 JSON セクション:

| セクション | 最小内容 |
| --- | --- |
| `system` | OS 名 / バージョン、CPU 名、物理 / 論理コア数、総メモリ、GPU 一覧または未検出理由 |
| `providers` | provider 種別、接続先概要、到達状態、probe 根拠、追加取得できた provider メタ |
| `model_candidates` | 登録名、provider 種別、provider 上の model ref、可用性状態 (`available` / `missing` / `unknown`)、判定根拠 |
| `summary` | provider 問題件数、model 可用性の集計、model-recommender prompt へ転記しやすい host facts の抜粋 |

Markdown 出力は上記 4 セクションを同順で人間可読に再構成する。`system` には v1.1.0 model-recommender prompt の必須ヒアリング項目 (provider, OS, CPU, メモリ, GPU, GPU 名, VRAM の判明分) に直接転記できる粒度を含める。

### CLI-00110 config lint

- ユーザー入力: 単一の設定ファイルまたは設定ディレクトリを主入力とし、必要時のみ補助設定ソースまたは Result Store 参照元を伴う
- 出力先: 検出された問題一覧を標準出力。問題が無い場合は「問題なし」を明示する
- 失敗表示: 静的検証問題または補助設定ソース不足は CLI-00303、引数の組合せ誤りは CLI-00302 を返す
- 責務境界: provider 通信、host hardware 収集、prompt 組立は行わない。単一ファイル入力でも、解決可能な静的相互参照までを扱う

主入力として扱う種別:

| 種別 | 最小責務 |
| --- | --- |
| Task Profile 定義 | Case / scorer 前提の静的整合性確認 |
| Model Candidate 定義 | provider_kind 参照の静的整合性確認 |
| Provider 接続情報 | 接続定義と認証情報ルールの静的整合性確認 |
| Run 設定 | Model Candidate / Task Profile 参照の静的整合性確認 |
| Comparison 設定 | Result Store に対する Run 参照整合性確認 |
| 設定ディレクトリ | 上記の横断整合性確認 |

### CLI-00111 config dry-run

- ユーザー入力: Run 設定を主入力とし、Task Profile / Model Candidate / Provider の補助設定ソースを解決する。host inventory は入力に含めない
- 出力先: 既定は標準出力。JSON を一次出力、Markdown は同一内容の派生表示とする
- 失敗表示: 静的読込失敗や補助設定ソース不足は CLI-00303、provider 到達不可・指定 model 未解決・代表 1 Case の prompt 組立不可は CLI-00308、致命的な内部失敗は CLI-00304 を返す
- 責務境界: provider 到達確認、指定 model ref 解決、代表 1 Case の prompt 組立可否までに限定する。実推論、採点、Result Store 書込、host facts 収集は行わない

最小 JSON セクション:

| セクション | 最小内容 |
| --- | --- |
| `run` | Run 設定の識別情報、解決された Model Candidate、対象 Task Profile 群、代表 Case |
| `probe` | provider 種別、接続先概要、到達状態、指定 model ref の解決状態 |
| `prompt_check` | 代表 Task Profile / Case、prompt 組立状態、provider request payload の最小メタ |
| `summary` | blocking issue 件数、Run 可否 (`ready` / `not_ready`)、次に進める操作 |

Markdown 出力は上記 4 セクションを同順で人間可読に再構成する。既定の public surface は、prompt 本文そのものではなく、代表 Case の識別子と組立状態を保証する。

### CLI-00112 provider status

- ユーザー入力: 1 件以上の Provider 接続情報。TaskProfile / Run / ModelCandidate は必須入力に含めない
- 出力先: 既定は標準出力。JSON を一次出力、Markdown は同一内容の派生表示とする
- 失敗表示: 到達不能 provider や inventory 未取得は 1 行 1 件で標準エラーへ表示し、command 自体が完了した場合でも終了コードで判定可能にする (CLI-00309)
- 責務境界: provider の起動状態、版情報、利用可能 model inventory の確認に限定する。host facts 収集、登録済み Model Candidate との照合、model pull / warmup は含めない

最小 JSON セクション:

| セクション | 最小内容 |
| --- | --- |
| `providers` | provider 種別、接続先概要、到達状態、版情報、利用可能 model inventory 要約 |
| `summary` | reachable / unreachable 件数、negative 判定、次に進める操作 |

Markdown 出力は上記 2 セクションを同順で人間可読に再構成する。

### CLI-00113 model pull

- ユーザー入力: 1 件の provider と 1 件の model target。target を登録済み ModelCandidate として解決してもよい
- 出力先: 進捗は標準エラー、最終結果は標準出力。JSON を一次出力、Markdown は同一内容の派生表示とする
- 失敗表示: 引数誤りは CLI-00302、設定解決失敗は CLI-00303、provider 側の pull 失敗は CLI-00304 を返す
- 責務境界: provider 側の model 取得要求に限定する。host facts 収集、prompt 組立、実採点、Result Store 書込は行わない

最小 JSON セクション:

| セクション | 最小内容 |
| --- | --- |
| `target` | provider 種別、接続先概要、要求した model target、解決済み ModelCandidate (該当時のみ) |
| `pull` | 最終状態 (`succeeded` / `already_present` / `failed`)、取得できた進捗要約、provider 根拠 |
| `summary` | 次に進める操作、blocking issue 件数 |

Markdown 出力は上記 3 セクションを同順で人間可読に再構成する。

### CLI-00114 model warmup

- ユーザー入力: 1 件の provider と 1 件の model target。TaskProfile / Run 設定は入力に含めない
- 出力先: 開始 / 完了通知は標準エラー、最終結果は標準出力。JSON を一次出力、Markdown は同一内容の派生表示とする
- 失敗表示: 引数誤りは CLI-00302、設定解決失敗は CLI-00303、warmup 実行失敗は CLI-00304 を返す
- 責務境界: command-scoped な最小 warmup 実行に限定する。Run 設定や代表 Case の prompt 組立、採点、Result Store 書込は行わない

最小 JSON セクション:

| セクション | 最小内容 |
| --- | --- |
| `target` | provider 種別、接続先概要、解決済み model target |
| `warmup` | 最終状態 (`ready` / `failed`)、経過時間、provider 根拠 |
| `summary` | 次に進める操作、blocking issue 件数 |

Markdown 出力は上記 3 セクションを同順で人間可読に再構成する。

## 事前確認・provider preparation サブコマンドの責務境界

| 面 | 主入力 | provider 通信 | 実推論 | 主目的 |
| --- | --- | --- | --- | --- |
| `check` | 設定ディレクトリ / Comparison 設定 | しない | しない | 既存互換の静的整合性確認 |
| `config lint` | 単一設定ファイル / 設定ディレクトリ | しない | しない | 利用者向け主導線の静的整合性確認 |
| `provider status` | Provider 接続情報 | する (read-only status) | しない | provider の起動状態 / 版情報 / inventory 確認 |
| `system-probe` | Provider / Model Candidate 定義 + host OS | する (read-only status) | しない | host snapshot と provider / model 可用性の横断観測 |
| `model pull` | Provider + 1 model target | する (acquire) | しない | model の明示取得 |
| `config dry-run` | Run 設定 + 補助設定ソース | する (read-only status) | しない | Run 固有 preflight と代表 1 Case の prompt 組立確認 |
| `model warmup` | Provider + 1 model target | する | する (minimal warmup のみ) | model のロード準備 |

provider 側準備を含む主導線は `provider status` → `model pull` → `model warmup` → `system-probe` → `config lint` → `config dry-run` → `run` とする。`check` は既存利用者との互換面として残し、`system-probe` / `config dry-run` は read-only な観測 / preflight、`model pull` / `model warmup` は explicit な preparation として併置する。

## 出力切替の責務境界

| ID | 規約 |
| --- | --- |
| CLI-00201 | 機械可読 (JSON) は Result Store の正準データを最小加工で出力する。人間可読 (Markdown 等) はその派生形とする |
| CLI-00202 | 出力形式の選択は CLI Entry が受け、レンダリングは Report Renderer (COMP-00012) が担う |
| CLI-00203 | 進捗表示と結果出力は別ストリームに分離する。結果のみを後段ツールへパイプ可能とする |
| CLI-00204 | 出力ファイルパスがユーザー指定された場合、CLI Entry はそれを Report Renderer に渡すだけで、内容を加工しない |
| CLI-00205 | `model pull` / `model warmup` の進捗表示は正準出力に含めない。標準エラー上の進捗は補助情報とし、最終結果のみを正準 JSON / Markdown とする |

## 終了コード方針

NFR-00003 の「原因の切り分けに必要な情報」を、終了コードでも識別可能にします。本書は終了コードの分類を定め、各分類は一意な数値に対応付けられるものとします。

| ID | 終了コード分類 | 用途 |
| --- | --- | --- |
| CLI-00301 | success | サブコマンドが目的を達成した。`check` / `config lint` で問題が検出されなかった場合を含む |
| CLI-00302 | user-input error | 引数誤り、未知 Run / Comparison 識別子、未知 Task / Model 参照など、ユーザー側で訂正可能なもの |
| CLI-00303 | configuration error | 設定読込失敗、整合性検証で問題検出 (`check` / `config lint` の問題検出、`config dry-run` の静的読込失敗を含む) |
| CLI-00304 | runtime error | Run 実行中や explicit provider operation 実行中の致命的失敗 (Result Store 書込不可、pull / warmup 失敗等 FLW-00102 相当) |
| CLI-00305 | partial-failure | Run は完了したが個別 Trial 失敗が含まれる (FUN-00204, FLW-00101)。スクリプトから「許容するか」を判定可能にする |
| CLI-00306 | comparison-incomplete | `compare` が一部 Run の不一致 (DAT-00109) や欠損ケースを検知して警告付きで完成した。スクリプトから不完全性を判定可能にする |
| CLI-00307 | probe-negative | `system-probe` が完了したが、到達不能 provider または可用性を確認できない Model Candidate が残った。スクリプトから preflight NG を判定可能にする |
| CLI-00308 | dry-run-negative | `config dry-run` は完了したが、provider 到達不可、指定 model 未解決、または代表 1 Case の prompt 組立不可が残った。スクリプトから Run 前 NG を判定可能にする |
| CLI-00309 | provider-status-negative | `provider status` が完了したが、到達不能 provider または inventory を取得できない provider が残った。スクリプトから provider 準備 NG を判定可能にする |

`partial-failure` を `success` と区別する点が本書の確定事項です。閾値設定 (失敗率 X% 以上で失敗扱い) は v1 では持ちません (OOS-00008 と整合)。

## 失敗時の表示方針

| ID | 方針 |
| --- | --- |
| CLI-00401 | 失敗は 1 行 1 失敗を原則とし、識別子 (Run / Task / Case / Model) と失敗種別 (PVD-) を含める |
| CLI-00402 | 復旧手順を要する失敗 (provider unreachable 等) は、ユーザーが取るべき確認項目を 1 行で添える |
| CLI-00403 | スタックトレースは既定で抑止し、明示フラグで開示する。本ツール内部のバグと provider 起因の失敗を混同させない |

## 拡張時の影響範囲

| 拡張 | 影響を受ける CLI- |
| --- | --- |
| 新サブコマンド追加 | CLI-00101 系列に新規 ID を追加 |
| 新出力形式 | CLI-00201〜00204 のうち該当する規約を更新 |
| 新終了コード分類 | CLI-00301 系列に新規 ID を追加 (既存値の意味は変えない) |
