# v1.2.0 リリース受入基準

2026-04-24 時点の v1.2.0 リリースタグに対する受入基準です。現行 public surface とスコープ境界を ID 単位に展開します。実装方法・スケジュールには踏み込みません。

v1.2.0 では既存の `run` / `report` / `compare` / `list` / `runs` / `comparisons` / `check` に加え、`provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run` を受入対象に含めます。

関連既存 ID: REQ-00001, REQ-00002, REQ-00003, FUN-001xx〜004xx, NFR-00001〜00602, OOS-00001〜00012, ARCH-00001〜00303, COMP-00001〜00012, CLI-00101〜00309, CFG-00101〜00610, PVD-00101〜00408, SCR-00101〜00810

## v1.2.0 で満たす要件

### 機能要件

| ID | 受入観点 (smoke レベル) |
| --- | --- |
| FUN-00101 | サンプル Task Profile 1 件を登録ファイルから読み込めること |
| FUN-00102 | 登録された Task Profile に Case 1 件以上が含まれること |
| FUN-00103 | サンプル Model Candidate 1 件以上を登録ファイルから読み込めること |
| FUN-00104 | `list` (CLI-00103) で登録済み Task Profile / Model Candidate が表示されること |
| FUN-00105 | 期待出力欠落・未知 provider 参照を `check` (CLI-00105) と `config lint` (CLI-00110) で検出できること |
| FUN-00207 | `run` (CLI-00106) が指定 Task Profile 群 × 1 Model Candidate を実行し Run 識別子を返すこと。2 件以上の Model 指定はエラーとして拒否されること |
| FUN-00202 | 試行回数 n を 1 以上で指定可能、結果に反映されること |
| FUN-00203 | 生成条件が Run メタとして保存されること |
| FUN-00204 | 1 Trial 失敗時に Run 全体が停止せず継続すること |
| FUN-00205 | 失敗 Trial が欠損として集計から除外されること (SCR-00501) |
| FUN-00206 | Run 完了時、Run 識別子で結果ディレクトリを参照できること |
| FUN-00307 | `report` (CLI-00102) が指定 Run の単一モデル集計を返すこと (ランキングを含まない) |
| FUN-00302 | 集計結果に品質スコア・応答時間・トークン消費の 3 軸が含まれること |
| FUN-00303 | n, mean, p50, p95 が表示されること (SCR-00401〜00404) |
| FUN-00308 | `compare` (CLI-00107) が品質重視 / 速度重視 / 統合の 3 軸でモデル横断ランキングを表示できること (SCR-00802〜00804) |
| FUN-00309 | 複数 Run 識別子を渡して Comparison を作成・取得できること。同一 TaskProfile セットでない場合は拒否されること (DAT-00109) |
| FUN-00310 | `compare` 実行時にランキング軸・重み上書きを指定できること |
| FUN-00305 | 機械可読 (JSON) と人間可読 (Markdown) の両出力が Run / Comparison 両方で選択可能 (CLI-00201) |
| FUN-00306 | 結果に生成条件と provider 識別が含まれること (PVD-00208) |
| FUN-00401 | `runs` (CLI-00104) で過去 Run 一覧が表示されること |
| FUN-00402 | `check` (CLI-00105) で Run 開始前検証が単独実行できること。Comparison 参照検証 (CFG-00506) を含む |
| FUN-00403 | `comparisons` (CLI-00108) で過去 Comparison 一覧が表示されること |
| FUN-00404 | `system-probe` (CLI-00109) が CPU / メモリ / GPU / OS と、設定済み provider の疎通結果を JSON / Markdown の両方で返すこと |
| FUN-00405 | `system-probe` (CLI-00109) が登録済み Model Candidate ごとに provider 上の可用性を返すこと |
| FUN-00406 | `config lint` (CLI-00110) が単一設定ファイルまたは設定ディレクトリを静的検証できること |
| FUN-00407 | `config dry-run` (CLI-00111) が Run 設定を起点に provider 疎通、指定 model 解決、代表 1 Case の prompt 組立可否を確認できること |
| FUN-00408 | `provider status` (CLI-00112) が provider の起動状態、版情報、利用可能モデル一覧を JSON / Markdown の両方で返すこと |
| FUN-00409 | `model pull` (CLI-00113) が 1 件の model target を明示取得でき、`run` / `system-probe` / `config dry-run` / `model warmup` が暗黙 pull しないこと |
| FUN-00410 | `model warmup` (CLI-00114) が 1 件の model target に最小の provider 実行を 1 回行い、TaskProfile / Run 設定に依存せずロード状態へ寄せられること |

### 非機能要件

| ID | 受入観点 (smoke レベル) |
| --- | --- |
| NFR-00001 | 開発者外の 1 名が、本書の主導線に従って初回 Run 完了まで 5 分以内に到達できること (1 回計測で確認) |
| NFR-00002 | 全主要操作が単一 CLI のサブコマンドから到達可能であること |
| NFR-00003 | 失敗時に「Run / Task / Case / Model / 失敗種別 (PVD-)」が出力されること (CLI-00401) |
| NFR-00004 | 人間可読出力の先頭にランキング表が現れること |
| NFR-00101 | 同一 Run 設定で 2 回実行し、集計値の n が一致すること (mean は LLM 揺れの範囲、p50/p95 は再現性指標として記録) |
| NFR-00102 | 結果ファイルに生成条件と provider 識別が含まれること |
| NFR-00103 | 結果ディレクトリに生応答 (PVD-00205) と集計値が分離保存されること |
| NFR-00201 | provider 追加が評価ロジック・結果スキーマを変更せず行えるよう、契約 (PVD-) のみで完結する設計であること |
| NFR-00202 | scorer 追加が既存 Task Profile の意味を変えないこと (SCR-00302) |
| NFR-00203 | Task Profile / Case がツール本体外のディレクトリから読み込めること (CFG-00301) |
| NFR-00204 | 結果スキーマに版識別子が含まれること (DAT-00201) |
| NFR-00301 | macOS / Linux のいずれかで全 smoke 観点が通ること |
| NFR-00302 | 外部依存導入が要件 ID に紐付けて記録されていること |
| NFR-00401 | 設定ファイルに認証情報の値が含まれないこと (CFG-00402 で検証) |
| NFR-00402 | 既定接続先が localhost であること (CFG-00204) |
| NFR-00501 | `run` 実行中に進捗が継続的に標準エラーへ出力されること |
| NFR-00502 | Run 失敗時、原因確認に使える情報 (PVD-00207 / 失敗 Trial) がファイルに残ること |
| NFR-00601 | 1 Trial あたりのツール内オーバーヘッドが 100ms 未満であることを smoke で 1 度確認 |
| NFR-00602 | 10 モデル × 10 Task Profile × 5 Trial を smoke 規模で実行し、結果ディレクトリ容量が常識的範囲に収まることを確認 |

## v1.2.0 smoke 観点チェックリスト

各観点は実装フェーズで TASK-NNNNN-XX として個別 task 化される前提の運用補足です。受入基準の各 ID が「smoke レベルで何を観察すれば満たしたと判断できるか」を 1 行ずつ記述します。

### 機能要件 (FUN-)

| ID | smoke 観察項目 |
| --- | --- |
| FUN-00101 | サンプル設定ディレクトリを指定して `list` 系操作で Task Profile 1 件が読み込まれて表示される |
| FUN-00102 | 上記 Task Profile に Case 1 件以上が紐付いて表示される |
| FUN-00103 | サンプル設定から Model Candidate 1 件以上が読み込まれて表示される |
| FUN-00104 | `list` サブコマンドで Task Profile / Model Candidate の両一覧が同一実行内で表示される |
| FUN-00105 | 期待出力欠落と未知 provider 参照を持つ不正設定に対し `check` と `config lint` の双方が失敗し、原因 ID を含むメッセージを返す |
| FUN-00207 | `run` サブコマンドで 1 モデル指定 + 1 Task Profile + n=3 で完走し、Run 識別子が返る。2 モデル同時指定は拒否される |
| FUN-00202 | `run` で n=1 と n=3 を実行し、結果集計のサンプル数 (n) が指定値と一致する |
| FUN-00203 | Run 完了後の結果に温度 / seed 等の生成条件が記録されている |
| FUN-00204 | 1 Trial を意図的に失敗させても残りの Trial が継続し、Run が完走する |
| FUN-00205 | 失敗 Trial を含む Run の集計で、失敗分が母数 (n) から除かれている |
| FUN-00206 | 返された Run 識別子から結果ディレクトリのパスを引ける |
| FUN-00307 | `report` で Run 識別子を渡すと単一モデル集計が返り、ランキング表は含まれない |
| FUN-00308 | 2 つの Run を `compare` で束ねた結果、品質軸 / 速度軸 / 統合軸でランキングが返る |
| FUN-00309 | 異なる TaskProfile セットの Run を `compare` に渡すと拒否され、Run 1 件のみ指定 (DAT-00108 / DAT-00109) も拒否される |
| FUN-00310 | `compare` 実行時にランキング軸と重みを CLI 引数で上書きでき、結果メタに反映される |
| FUN-00305 | `run` 結果と `compare` 結果の双方で JSON / Markdown 出力を選択できる |
| FUN-00306 | 結果ファイル内に生成条件と provider 識別 (provider 種別 + provider 上のモデル参照) が含まれる |
| FUN-00401 | `runs` で過去 Run が一覧表示される (1 件以上を観察) |
| FUN-00402 | `check` を Run 実行とは独立に呼び出して結果が得られ、Comparison 参照検証 (CFG-00506) も走る |
| FUN-00403 | `comparisons` で過去 Comparison が一覧表示される (1 件以上を観察) |
| FUN-00404 | `system-probe` が `system` / `providers` / `model_candidates` / `summary` の 4 セクションを返し、OS / CPU / メモリ / GPU と provider 疎通が JSON / Markdown の双方で観察できる |
| FUN-00405 | `system-probe` が登録済み Model Candidate ごとに `available` / `missing` / `unknown` を返し、判定根拠が追える |
| FUN-00406 | `config lint` が設定ディレクトリ全体と単一設定ファイルの両方を検証でき、静的問題を終了コード付きで返す |
| FUN-00407 | `config dry-run` が Run 設定を起点に provider 到達、指定 model 解決、代表 1 Case の prompt 組立可否を返し、実推論・採点・Result Store 書込を行わない |
| FUN-00408 | `provider status` が provider ごとの到達状態、版情報、利用可能 model inventory を JSON / Markdown の双方で返す |
| FUN-00409 | `model pull` が 1 件の model target について取得結果と進捗を返し、`run` / `system-probe` / `config dry-run` / `model warmup` が暗黙 pull しない |
| FUN-00410 | `model warmup` が 1 件の model target に対して minimal warmup を 1 回だけ実行し、`ready` / `failed` と経過時間を返す。TaskProfile / Run 設定は不要 |

### 非機能要件 (NFR-)

| ID | smoke 観察項目 |
| --- | --- |
| NFR-00001 | サンプル構成と既定の主導線を使い、初回 Run 完了までの操作を 5 分以内で実演できる (1 回計測) |
| NFR-00002 | smoke 観点の全操作 (`provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run` / `run` / `report` / `compare` / `list` / `runs` / `comparisons` / `check`) が単一 CLI のサブコマンドから到達できる |
| NFR-00003 | 失敗 Trial を発生させた Run の出力に Run / Task / Case / Model / 失敗種別 (PVD-) の 5 要素が揃う |
| NFR-00004 | `compare` の人間可読出力の先頭にランキング表が現れる |
| NFR-00101 | 同一 Run 設定で 2 回実行し、両 Run の集計値 n が一致する (mean は LLM 揺れ範囲、p50/p95 は記録のみ) |
| NFR-00102 | 結果ファイルから生成条件と provider 識別の両者を grep で確認できる |
| NFR-00103 | 結果ディレクトリ内で生応答と集計値が別ファイル (または別ディレクトリ) に分かれて保存される |
| NFR-00201 | provider を 1 件追加するシナリオを設計レビュー上で辿り、評価ロジック・結果スキーマに変更が及ばないことを確認する |
| NFR-00202 | scorer を 1 件追加するシナリオを設計レビュー上で辿り、既存 Task Profile の意味が不変であることを確認する |
| NFR-00203 | ツール本体ディレクトリ外に置いた Task Profile / Case を CLI 引数経由で読み込んで Run が完走する |
| NFR-00204 | 結果ファイルに版識別子 (DAT-00201) フィールドが含まれる |
| NFR-00301 | macOS または Linux いずれか 1 環境で本チェックリストの全 smoke 観点が通る |
| NFR-00302 | 導入済み外部依存の一覧と紐付く要件 ID が development ドキュメントから参照できる |
| NFR-00401 | サンプル設定ファイル群を grep して認証情報の値が現れないこと、および `config lint` が値を含む設定を検出して失敗することを確認する |
| NFR-00402 | 既定接続先 (CFG-00204) が localhost であることを `provider status` / `system-probe` / `config dry-run` の既定動作または既定値表示から確認する |
| NFR-00501 | `run` 実行中に進捗が標準エラーへ継続出力されることを目視確認する |
| NFR-00502 | 失敗 Trial を含む Run の結果ディレクトリに provider 生応答 (PVD-00207) と失敗 Trial 情報がファイルとして残る |
| NFR-00601 | smoke で 1 Trial を計測し、ツール内オーバーヘッド (provider 呼び出し外の時間) が 100ms 未満であることを 1 回観察する |
| NFR-00602 | 10 モデル × 10 Task Profile × 5 Trial 規模を 1 回実行し、結果ディレクトリ容量が常識的範囲 (例: 数百 MB 以内) に収まることを確認する |

## 検証の方針

- 受入は smoke レベルで足りる。網羅テスト・性能ベンチを v1.2.0 受入条件にしない
- 検証は単一の検証 task (project-master が起票) に集約し、上記 ID を逐一参照する
- 受入で未達の ID は後段リリースへ移送するか、機能の縮小で対処する。要件側の意味は変えない

## 明示的な未対応 (OOS-)

v1.2.0 では以下を満たさない。公開面と smoke 判定はこの境界を前提にする。

| ID | 未対応の内容 |
| --- | --- |
| OOS-00001 | Ollama 以外の provider |
| OOS-00002 | streaming 経由の TTFT / decode TPS |
| OOS-00003 | RAM / GPU メモリ計測 |
| OOS-00004 | LLM-as-a-Judge による自動採点 |
| OOS-00005 | (superseded by OOS-00012) モデルの自動 download / pull |
| OOS-00006 | provider プロセスの起動・停止管理 |
| OOS-00007 | チーム共有を前提とした結果ストア |
| OOS-00008 | CI 組み込み用の閾値 gate |
| OOS-00009 | Run の途中再開 / 失敗 Case のみ再実行 |
| OOS-00010 | クラウド有料モデル評価・課金推定 |
| OOS-00011 | Copilot CLI を LLM-as-a-Judge として活用する検討 |
| OOS-00012 | `run` / `system-probe` / `config dry-run` / `model warmup` からの暗黙 model pull |

## 後段リリースとの境界

| 移送先 | 主な ID 群 (現時点の方針) |
| --- | --- |
| v2.0.0 | OOS-00002, OOS-00003, OOS-00004, チーム共有を伴う結果ストア (OOS-00007 の見直し) |
| 版未定 | OOS-00008, OOS-00009, OOS-00010, OOS-00011 |

ロードマップ更新時は本書の対応表を併せて更新します。
