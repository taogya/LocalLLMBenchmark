# 06. 設定ソース (Configuration Sources)

Configuration Loader (COMP-00007) / Task Catalog (COMP-00008) / Result Store (COMP-00009) が読み書きする物理ファイル群を、概念単位で定義します。本書は「どの種別のファイルが、どこに、誰の所有で、何を含むか」を定め、個々のキー名や Result Store の物理スキーマ詳細は扱いません。

関連既存 ID: REQ-00001, FUN-00101, FUN-00102, FUN-00103, FUN-00105, FUN-00203, FUN-00207, FUN-00309, FUN-00402, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408, FUN-00409, FUN-00410, NFR-00203, NFR-00302, NFR-00401, NFR-00402, ARCH-00005, ARCH-00006, ARCH-00303, COMP-00007, COMP-00008, COMP-00009, COMP-00011, DAT-00001, DAT-00002, DAT-00003, DAT-00008, DAT-00009, FLW-00003, FLW-00007, FLW-00008, FLW-00009, FLW-00010, FLW-00011, FLW-00012

## 設計原則

| ID | 原則 |
| --- | --- |
| CFG-00001 | ユーザーが定義する素材 (Task Profile / Case / Model Candidate) はツール本体と物理的に分離可能とする (ARCH-00005, NFR-00203) |
| CFG-00002 | 認証情報はファイル中に平文で保持しない。環境変数経由でのみ解決する (NFR-00401, ARCH-00303) |
| CFG-00003 | 設定ファイルは人間が手で書けるテキスト形式とし、階層構造を表現できること |
| CFG-00004 | 1 ファイル 1 概念とし、複数概念を 1 ファイルに混在させない |

## ファイル種別

各ファイル種別の所在は「既定パス」と「ユーザー指定パス」の両方を許可します。既定パスはツール本体の隣に置かれ、ユーザー指定パスはツール本体の外に置けます (BYO データ)。

| ID | 種別 | 概念上の内容 | 所有者 | 主な読み手 |
| --- | --- | --- | --- | --- |
| CFG-00101 | Task Profile 定義 | TaskProfile (DAT-00001) と Case 群 (DAT-00002) | ユーザー | COMP-00008 Task Catalog |
| CFG-00102 | Model Candidate 定義 | ModelCandidate (DAT-00003) の集合 | ユーザー | COMP-00007 Configuration Loader |
| CFG-00103 | (superseded by CFG-00107) Run 設定 | Run 単位の生成条件 (温度・seed・最大トークン等) と試行回数の既定値。複数 Model を含む設定を許していた | ユーザー | COMP-00007 → COMP-00003 |
| CFG-00104 | Provider 接続情報 | provider 種別ごとの接続先 (例: Ollama の host/port) | ユーザー | COMP-00007 → COMP-00005 |
| CFG-00105 | 認証情報の解決ルール | 環境変数名と用途の対応のみ。値は本ファイルに含めない | ユーザー (環境変数の実値) | COMP-00007 |
| CFG-00106 | Result Store ルート | Run / Comparison 結果ディレクトリを置く起点 | ユーザー | COMP-00009 |
| CFG-00107 | Run 設定 (1 Run = 1 Model) | 1 件の Model Candidate 参照、Run 単位の生成条件、試行回数の既定値 (DAT-00008) | ユーザー | COMP-00007 → COMP-00010 |
| CFG-00108 | Comparison 設定 | 1 件以上の Run 識別子集合、ランキング軸の既定、重み上書き (DAT-00009) | ユーザー | COMP-00007 → COMP-00011 |

注:
- CFG-00101〜00104 はそれぞれ別ファイルとし、相互参照は識別子 (名称) で行う。
- CFG-00105 はファイルに「環境変数名」だけを書き、実値はファイルに書かない。
- 既定ではすべて単一の設定階層から読み出されるが、ユーザー指定により外部ディレクトリを差し替え可能とする。
- `system-probe` は CFG-00102 と CFG-00104 を突き合わせ、provider 側の外部状態に照らして可用性を観測する。

## 必須/任意項目 (概念リスト)

本節では設定種別ごとの最小概念項目だけを示します。個々のキー名や表記上の省略記法は本書の対象外とします。

### CFG-00201 Task Profile 定義

| 区分 | 概念項目 |
| --- | --- |
| 必須 | 名称 (識別子)、用途カテゴリ、評価契約 (使用 scorer の名前と引数)、Case 1 件以上 |
| 任意 | 説明、想定モデル種別、補助メタ |

Case の必須項目: 入力データ。期待出力は scorer が必要とする場合のみ必須。

### CFG-00202 Model Candidate 定義

| 区分 | 概念項目 |
| --- | --- |
| 必須 | 名称 (識別子)、provider 種別、provider 上のモデル参照 |
| 任意 | 表示用ラベル、想定パラメータ規模等のメタ |

`system-probe` はこの provider 上のモデル参照を provider 側で解決し、可用性状態に写像する。存在確認は静的整合性検証ではなく動的 probe に属する。

### CFG-00203 (superseded by CFG-00206) Run 設定

複数 Model Candidate を含む設定を許していたため supersede。新 ID は CFG-00206。

### CFG-00204 Provider 接続情報

| 区分 | 概念項目 |
| --- | --- |
| 必須 | provider 種別、接続先 (既定は localhost) |
| 任意 | タイムアウト既定値、リトライ方針 |

外部送信を伴う接続先は明示設定なしには許可しない (NFR-00402)。
`system-probe` と `provider status` は、この接続先を用いて provider との read-only status / probe を行う。`model pull` と `model warmup` も同じ接続先を使う。

### CFG-00205 認証情報の解決ルール

| 区分 | 概念項目 |
| --- | --- |
| 必須 | 用途 (provider 種別 / 機能) と参照する環境変数名の対応 |
| 禁止 | 値そのもの、ハッシュ済み値、難読化済み値 |

認証情報を要求する provider の追加時は、本ファイルに環境変数名のエントリを追加することで対応する。

### CFG-00206 Run 設定 (1 Run = 1 Model)

| 区分 | 概念項目 |
| --- | --- |
| 必須 | 1 件の Model Candidate 参照、試行回数 n (1 以上) |
| 任意 | 温度・seed・最大トークン等の生成条件既定値 |

複数 Model Candidate 参照は Configuration Loader が不整合として拒否する。ランキング軸の既定は Run 設定から除き、Comparison 設定 (CFG-00207) へ移した。生成条件は Run 開始後に変更されない (DAT-00105)。

### CFG-00207 Comparison 設定

| 区分 | 概念項目 |
| --- | --- |
| 必須 | 2 件以上の Run 識別子集合 (DAT-00108 / DAT-00109) |
| 任意 | ランキング軸の既定 (品質重視 / 速度重視 / 統合)、統合軸の重み上書き、表示ラベル |

Comparison 設定を CLI 引数で上書きした場合、上書き値は Comparison メタに記録される (FUN-00310)。

## BYO データの分離方針

| ID | 規約 |
| --- | --- |
| CFG-00301 | Task Profile 定義 (CFG-00101) と Case ファイル群はツール本体のディレクトリ外に置ける (ARCH-00005, NFR-00203) |
| CFG-00302 | Configuration Loader は「ツール本体側既定」と「ユーザー指定外部」のどちらから読んだかを Run メタに記録する (FUN-00306 を補助) |
| CFG-00303 | ユーザー定義素材を更新しても、ツール本体のバージョンに影響を与えない |

## 認証情報の取り扱い

| ID | 規約 |
| --- | --- |
| CFG-00401 | 認証情報は環境変数経由でのみ取得する (NFR-00401) |
| CFG-00402 | 設定ファイル中で値を平文・難読化を問わず保持することを禁止する。Configuration Loader は検出時に整合性検証で失敗を返す |
| CFG-00403 | 認証情報は Configuration 層のメモリ内にのみ保持し、Result Store および進捗表示への漏出を禁止する (ARCH-00303) |
| CFG-00404 | `check` (CLI-00105) は、必要な環境変数が解決可能かまでを検証し、値そのものは出力しない |

## 整合性検証の責務

`check` (CLI-00105) / `config lint` (CLI-00110) と Run 開始前検証 (FLW-00102) は同じ Configuration Loader を使います。provider 到達確認や Model Candidate 可用性の観測は、本節の静的検証には含めません。

| ID | 検証項目 |
| --- | --- |
| CFG-00501 | Task Profile が必須項目 (CFG-00201) を満たすか |
| CFG-00502 | Model Candidate の provider 種別が登録済み provider 集合に含まれるか |
| CFG-00503 | 評価契約が参照する scorer が SCR- に存在するか |
| CFG-00504 | 認証情報を要求する provider に対して、対応する環境変数が解決可能か (値の中身は検証しない) |
| CFG-00505 | Result Store ルート (CFG-00106) が書込可能か |
| CFG-00506 | Comparison 設定 (CFG-00207) が参照する Run 識別子が 2 件以上 (DAT-00108) で Result Store に存在し、TaskProfile セットが一致するか (DAT-00109) |

## 診断系入力の単位

| ID | 規約 |
| --- | --- |
| CFG-00604 | `config lint` は設定ディレクトリ全体または単一設定ファイルを主入力にできる。単一ファイルの対象は CFG-00101 / CFG-00102 / CFG-00104 / CFG-00107 / CFG-00108 に限る |
| CFG-00605 | 単一ファイル入力が相互参照を持つ場合、`config lint` は明示指定または標準配置から導出できる補助設定ソースだけを読む。補助ソースが解決できない場合は検証省略ではなく設定エラーとして報告する |
| CFG-00606 | `config dry-run` は CFG-00107 (Run 設定) を主入力とし、CFG-00101 / CFG-00102 / CFG-00104 を補助ソースとして解決する。host inventory と CFG-00108 は要求しない |
| CFG-00607 | `config dry-run` は Run の実行順から決まる代表 1 Case の prompt 組立可否までを確認する。実推論、採点、Result Store 書込は行わない |

| 主入力 | 必要な補助ソース | 静的に確認する範囲 |
| --- | --- | --- |
| 設定ディレクトリ | なし | Task Profile / Model Candidate / Provider の横断整合性 |
| Task Profile 定義 | なし | Case / scorer 前提の整合性 |
| Model Candidate 定義 | Provider 接続情報 | provider_kind 参照の整合性 |
| Provider 接続情報 | なし | 接続定義と認証情報ルール |
| Run 設定 | Task Profile 定義 / Model Candidate 定義 / Provider 接続情報 | Run 参照と生成条件の整合性 |
| Comparison 設定 | Result Store ルート | Run 実在性と TaskProfile セット整合性 |

## 動的 probe の責務境界

| ID | 規約 |
| --- | --- |
| CFG-00601 | `system-probe` は CFG-00102 (Model Candidate) と CFG-00104 (Provider 接続情報) のみを必須入力とし、CFG-00101 / CFG-00107 / CFG-00108 を要求しない |
| CFG-00602 | provider 到達確認と Model Candidate 可用性は外部状態の観測であり、静的な設定妥当性そのものではない。`check` と `config lint` は provider 通信を行わない |
| CFG-00603 | `system-probe` の入力境界は `config dry-run` 追加後も維持し、Run 設定と TaskProfile を必須入力に持ち込まない |

## provider preparation の入力境界

| ID | 規約 |
| --- | --- |
| CFG-00608 | `provider status` は CFG-00104 (Provider 接続情報) のみを必須入力とし、CFG-00102 / CFG-00101 / CFG-00107 / CFG-00108 を要求しない |
| CFG-00609 | `model pull` と `model warmup` は 1 件の Provider 接続情報と 1 件の command-scoped model target を入力にする。target を登録済み ModelCandidate として指定する場合に限り、CFG-00102 を補助ソースとして解決してよい |
| CFG-00610 | `model warmup` は command-scoped な最小 warmup input を用い、CFG-00107 の generation 既定値や TaskProfile / Case 由来の prompt 組立を読まない |

## 拡張時の影響範囲

| 拡張 | 影響を受ける CFG- |
| --- | --- |
| 新 provider 追加 | CFG-00204 / CFG-00205 / CFG-00502 |
| 新 scorer 追加 | CFG-00201 (任意) / CFG-00503 |
| 新メタ項目 | 該当ファイル種別の任意項目に追加。必須項目の追加は版識別子 (DAT-00201) の更新を伴う |
