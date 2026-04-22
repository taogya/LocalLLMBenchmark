# 08. 採点とランキング (Scoring and Ranking)

v1 同梱の Quality Scorer (COMP-00006) の語彙、統計集計、ランキング算出を概念定義します。Python 実装名・関数シグネチャは扱いません。

関連既存 ID: REQ-00001, REQ-00002, FUN-00302, FUN-00303, FUN-00308, FUN-00309, FUN-00310, FUN-00305, NFR-00004, NFR-00101, NFR-00202, ARCH-00004, ARCH-00202, ARCH-00206, COMP-00004, COMP-00006, COMP-00011, COMP-00012, DAT-00005, DAT-00006, DAT-00009, DAT-00010, DAT-00011, DAT-00104, FLW-00002, FLW-00006

## 設計原則

| ID | 原則 |
| --- | --- |
| SCR-00001 | scorer は決定的とする。同一入力に対し同一出力を返す。LLM-as-a-Judge は v1 では持たない (OOS-00004, OOS-00011) |
| SCR-00002 | scorer の結果は数値域 [0.0, 1.0] または bool に正規化する。bool は集計時に 0.0 / 1.0 とみなす |
| SCR-00003 | (superseded by SCR-00802) ランキングは品質と性能の独立軸を持ち、ユーザーが軸を切替えられる (FUN-00304)。ランキングは Run スコープではなく Comparison スコープに移動したため supersede |
| SCR-00004 | 統計集計は CaseAggregation (DAT-00006) のみを介して行う。Trial 個別値への直接参照を許さない (DAT-00106) |

## v1 同梱 scorer の語彙

個人ユーザーが用途を定義するのに必要十分な決定的 scorer を選定します。各 scorer は Task Profile の評価契約から名前で参照されます (CFG-00503)。

| ID | scorer (概念名) | 入力 (期待値の形式) | 出力 | 想定用途 |
| --- | --- | --- | --- | --- |
| SCR-00101 | exact_match | 期待文字列 1 件 | bool | 厳密一致 (短回答 / 分類ラベル) |
| SCR-00102 | normalized_match | 期待文字列 1 件 + 正規化方針 (大小文字・前後空白・全半角の畳み込み) | bool | 表記ゆれを吸収した一致 |
| SCR-00103 | regex_match | 正規表現 1 件 | bool | 形式が決まる出力 (識別子・コード等) |
| SCR-00104 | contains | 期待部分文字列 1 件以上 (AND / OR を概念で指定) | bool | 必須語の含有確認 |
| SCR-00105 | json_valid | (期待値なし) または期待スキーマ概念 | bool | 構造化出力の妥当性 |
| SCR-00106 | length_within | 最小・最大の文字数または語数 | bool | 長さ制約 (要約等) |
| SCR-00107 | numeric_close | 期待数値 + 許容差 (絶対 / 相対) | bool | 数値抽出・計算系 |

入出力に関する共通ルール:

| ID | 規約 |
| --- | --- |
| SCR-00201 | scorer の入力は応答テキスト (PVD-00201) と期待出力 (Case が持つもの) のみ。生応答 (PVD-00205) は scorer に渡さない |
| SCR-00202 | scorer は失敗を例外で表現せず、`scoring 適用不可` (PVD-00307) を Provider Adapter 側の失敗種別と同じ語彙で返す |
| SCR-00203 | bool を返す scorer は集計時に 0.0 / 1.0 として扱う。0..1 連続値を返す scorer の追加は SCR-00108 以降で扱う |

新 scorer 追加時のルール:

| ID | 規約 |
| --- | --- |
| SCR-00301 | 追加 scorer は本書に新 ID を採番して登録する |
| SCR-00302 | 追加によって既存 Task Profile の意味が変わってはならない (NFR-00202) |

## 統計集計

CaseAggregation (DAT-00006) と Run 集計の算出を定義します。

| ID | 集計値 | 定義 |
| --- | --- | --- |
| SCR-00401 | n | 当該 Case × ModelCandidate における **成功 Trial 数** (DAT-00104) |
| SCR-00402 | mean | 成功 Trial の品質スコアと性能 metric それぞれの算術平均 |
| SCR-00403 | p50 | 成功 Trial の中央値。サンプル数偶数時は線形補間 |
| SCR-00404 | p95 | 成功 Trial の 95 パーセンタイル。線形補間で算出 |
| SCR-00405 | failure_count | 失敗 Trial 数。失敗種別 (PVD-) 別の内訳を保持 |

欠損 Trial の扱い:

| ID | 規約 |
| --- | --- |
| SCR-00501 | 失敗 Trial は集計値の母数 (n) に含めない (DAT-00104) |
| SCR-00502 | 全 Trial が失敗した場合、当該 CaseAggregation は値を欠損として表現し、ランキングからも除外する |
| SCR-00503 | 一部 Trial 成功の場合、成功分だけで集計し、failure_count を併記する |

性能 metric の集計対象は応答時間 (PVD-00202) と出力トークン数 (PVD-00204) を主軸とする。出力トークン数が provider から得られない場合、当該 metric は欠損として扱う。

## ランキング算出

Run Comparator (COMP-00011) が ComparisonReport (DAT-00011) を生成する際に適用します。ランキングは Run スコープではなく Comparison スコープで算出し、複数 Run に属するモデルサマリを入力とします。

### 軸の定義 (supersede 前は Run スコープ)

| ID | 軸 | 概念定義 |
| --- | --- | --- |
| SCR-00601 | (superseded by SCR-00802) 品質重視 (Run) | Run 内モデル横断を前提としていたため Comparison スコープで再定義 |
| SCR-00602 | (superseded by SCR-00803) 速度重視 (Run) | 同上 |
| SCR-00603 | (superseded by SCR-00804) 統合 (Run) | 同上 |

### Comparison スコープの軸

| ID | 軸 | 概念定義 |
| --- | --- | --- |
| SCR-00802 | 品質重視 (Comparison) | Comparison に含まれるモデル別に、品質スコアの mean を主、p50 を副に並べる。同点時は SCR-00809 のタイブレーカーへ |
| SCR-00803 | 速度重視 (Comparison) | Comparison に含まれるモデル別に、応答時間 mean が小さい順。同 mean の場合は p95 が小さい順 |
| SCR-00804 | 統合 (Comparison) | 品質と速度を SCR-00805 の重みで合成したスコア降順 |

### SCR-00805 統合スコアの算出 (Comparison スコープ)

統合スコアは Comparison 内で以下のとおり算出する (SCR-00604 は superseded by SCR-00805)。

1. 品質サブスコア = ModelCandidate ごとの品質 mean (Comparison 内全 Case 平均)。値域 [0.0, 1.0]
2. 速度サブスコア = ModelCandidate ごとの応答時間 mean を Comparison 内で相対正規化 (Comparison 内最速モデルを 1.0、その他は `最速 mean / 当該 mean`)。値域 (0.0, 1.0]
3. 統合スコア = `w_quality × 品質サブスコア + w_speed × 速度サブスコア`

| ID | 既定値 | 値 |
| --- | --- | --- |
| SCR-00604 | (superseded by SCR-00805) 統合スコアの算出 (Run スコープ) | Comparison スコープへ移動 |
| SCR-00605 | (superseded by SCR-00806) w_quality (品質重み既定) | 0.7 |
| SCR-00606 | (superseded by SCR-00807) w_speed (速度重み既定) | 0.3 |
| SCR-00607 | (superseded by SCR-00808) 重みのユーザー上書き (Run) | Comparison スコープへ移動 |
| SCR-00806 | w_quality (品質重み既定、Comparison) | 0.7 (この既定値は v1 smoke 後に再評価する) |
| SCR-00807 | w_speed (速度重み既定、Comparison) | 0.3 (この既定値は v1 smoke 後に再評価する) |
| SCR-00808 | 重みのユーザー上書き (Comparison) | Comparison 設定 (CFG-00207) または `compare` 実行時に 0..1 の浮動小数を指定可能。合計 1.0 を強制しない (内部で正規化) |

### SCR-00701 (superseded by SCR-00809) タイブレーカー (Run スコープ)

Run スコープで記述していたため supersede。

### SCR-00809 タイブレーカー (Comparison スコープ)

3 軸のいずれかで同点が発生した場合、以下の優先順で順位を確定する。

1. 品質サブスコアの mean (高いほうが上位)
2. 応答時間 mean (小さいほうが上位)
3. 出力トークン数 mean (小さいほうが上位)
4. ModelCandidate 名称の辞書順 (決定性確保のため)

### SCR-00801 (superseded by SCR-00810) 性能の正規化方針 (Run スコープ)

Run スコープで記述していたため supersede。

### SCR-00810 性能の正規化方針 (Comparison スコープ)

絶対秒は機械可読出力 (FUN-00305) と人間可読出力に常に併記する。ランキング統合軸 (SCR-00804) でのみ Comparison 内相対正規化 (SCR-00805) を用いる。Comparison 間比較を相対値で行わない。

## 拡張時の影響範囲

| 拡張 | 影響を受ける SCR- |
| --- | --- |
| 新 scorer 追加 | SCR-00108 以降に追加。SCR-00203 を満たすか確認 |
| 新ランキング軸 | SCR-00811 以降に追加。既存軸の意味は変えない |
| 連続値 scorer の重み付け | SCR-00805 の合成式を版識別子 (DAT-00201) 更新付きで拡張 |
| Run 間比較 (トレンド) | 本書の対象外。v1.1 以降で別 ID 体系を新設 |
