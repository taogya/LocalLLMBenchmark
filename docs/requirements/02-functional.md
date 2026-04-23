# 02. 機能要件 (Functional Requirements)

ユーザーが本ツールでできる操作を、機能単位で定義します。実装方法には踏み込みません。実装トレーサビリティは [development/traceability.md](../development/traceability.md) を参照してください。

## 構成

機能要件は次の 4 グループに分けます。

- 登録系 (FUN-001xx): ユーザーが定義する素材を扱う
- 実行系 (FUN-002xx): ベンチマークを動かす
- 結果系 (FUN-003xx): 結果を見る・比較する
- 補助系 (FUN-004xx): 確認・診断

## 登録系

| ID | 機能 |
| --- | --- |
| FUN-00101 | ユーザーは Task Profile を登録できる。Task Profile は名称、説明、用途カテゴリ、評価契約、1 件以上の Case を持つ |
| FUN-00102 | ユーザーは Case を Task Profile に追加できる。Case は入力データと期待出力 (該当する場合) を持つ |
| FUN-00103 | ユーザーは Model Candidate を登録できる。provider 種別と provider 上の識別子を最低限の構成要素とする |
| FUN-00104 | ユーザーは登録済み Task Profile / Model Candidate の一覧を確認できる |
| FUN-00105 | 登録内容に明らかな不整合 (期待出力欠落、未知 provider 参照など) がある場合、登録時点で検知できる |

## 実行系

| ID | 機能 |
| --- | --- |
| FUN-00201 | (superseded by FUN-00207) ユーザーは「実行する Task Profile 群」と「比較する Model Candidate 群」を指定して Run を開始できる |
| FUN-00202 | Run は同一 Case を複数回 (n 回) 実行できる。n は Run 開始時に指定できる |
| FUN-00203 | Run の生成条件 (温度・seed 等) は Run 単位で記録される |
| FUN-00204 | Run 中に個別 Case が失敗しても、他 Case の実行は継続される |
| FUN-00205 | 失敗した Case は失敗として記録され、後段の集計で欠損として扱われる |
| FUN-00206 | Run 完了時、結果は永続化され Run 識別子で参照可能になる |
| FUN-00207 | ユーザーは「実行する Task Profile 群」と「1 件の Model Candidate」を指定して Run を開始できる。1 Run = 1 Model とし、複数モデル比較は Run を複数回実行して Comparison (FUN-00309) で束ねる (REQ-00001, REQ-00003, NFR-00303 と整合) |

## 結果系

| ID | 機能 |
| --- | --- |
| FUN-00301 | (superseded by FUN-00307) ユーザーは Run 識別子を指定して、その Run の集計結果を確認できる |
| FUN-00302 | 集計結果は最低限「品質スコア」「応答時間」「トークン消費」の 3 軸を含む |
| FUN-00303 | 複数 Trial がある Case は、サンプル数・平均・p50・p95 を含む集計値で表示される |
| FUN-00304 | (superseded by FUN-00308) 結果はモデル別にランキング表示できる。ランキングは「品質重視」「速度重視」など複数の軸でソートできる |
| FUN-00305 | 結果は機械可読形式 (JSON) と人間可読形式 (Markdown) の両方で取得できる |
| FUN-00306 | Run 全体および主要 metric には、後段で意味を再解釈できる程度のメタ情報 (生成条件・provider 識別) が付与される |
| FUN-00307 | ユーザーは Run 識別子を指定して、単一モデル分の集計結果 (品質・応答時間・トークン消費・Case 別集計) を確認できる。ランキングは含まない (REQ-00002) |
| FUN-00308 | ユーザーは Comparison 識別子を指定して、束ねられた Run 群のモデル別ランキングを表示できる。ランキングは複数の軸 (品質重視・速度重視・統合) で切替可能 (REQ-00002) |
| FUN-00309 | ユーザーは複数の Run 識別子を指定して Comparison を作成できる。Comparison は同一 Task Profile セットを対象とする Run 群を束ね、モデル横断のランキング成果物を生成する (REQ-00002) |
| FUN-00310 | ユーザーは Comparison 表示時にランキング軸 (品質重視・速度重視・統合および重み) を実行時に切替えられる (REQ-00002) |

## 補助系

| ID | 機能 |
| --- | --- |
| FUN-00401 | ユーザーは過去 Run の一覧を確認できる |
| FUN-00402 | ユーザーは設定および登録内容の整合性を、Run 実行前に確認できる |
| FUN-00403 | ユーザーは過去 Comparison の一覧を確認できる |
| FUN-00404 | ユーザーは実行環境の CPU / メモリ / GPU / OS と、設定済み provider の疎通状態を、機械可読 / 人間可読の両方で確認できる |
| FUN-00405 | ユーザーは `model_candidates.toml` に登録した各 Model Candidate について、provider 上の可用性を実行前に確認できる |
| FUN-00406 | ユーザーは単一の設定ファイルまたは設定ディレクトリを指定して、静的整合性を実行前に確認できる |
| FUN-00407 | ユーザーは Run 設定を起点に、provider 疎通、指定 model の解決可否、代表 1 Case の prompt 組立可否を実行前に確認できる |
| FUN-00408 | ユーザーは設定済み provider について、起動状態、版情報、利用可能モデル一覧を実行前に確認できる |
| FUN-00409 | ユーザーは 1 件の provider 上の model ref を、明示コマンドで取得できる。`run` / `system-probe` / `config dry-run` / `model warmup` は暗黙に pull しない |
| FUN-00410 | ユーザーは 1 件の provider 上の model ref に対して、最小の provider 実行を 1 回行い、Run 前にロード状態へ寄せられる。TaskProfile / Run 設定への依存は持ち込まない |

## 関連の非機能要件

ユーザー体験・再現性・拡張容易性に関する要件は [03-non-functional.md](03-non-functional.md) を参照してください。
