# 07. Provider 契約 (Provider Contract)

Provider Adapter (COMP-00005) が満たすべき概念契約を定義します。HTTP エンドポイント名・スキーマ JSON・関数シグネチャは扱いません。v1 の唯一の実装は Ollama (localhost) ですが、本契約は Ollama 単体に最適化しません (NFR-00201)。

関連既存 ID: REQ-00001, FUN-00203, FUN-00207, FUN-00302, FUN-00306, NFR-00102, NFR-00201, NFR-00303, NFR-00402, NFR-00502, ARCH-00002, ARCH-00201, ARCH-00207, COMP-00005, DAT-00003, DAT-00005, FLW-00005, FLW-00101

## 1 Run = 1 Model 前提

本契約は 1 Run = 1 Model (FUN-00207, ARCH-00207) を前提とする。Run 中に Provider Adapter が扱う ModelCandidate は 1 件に限定され、モデル swap 起因のレイテンシ混入を送り込まない。これにより、provider プロセスが「モデルを常駐させて推論を受付するスタイル」 (LM Studio / OpenAI 互換 / llama.cpp server など OOS-00001 で后続検討とした provider 群) と高い親和性を保てる。ユーザーは必要に応じて provider 上でモデルを入れ替え、複数回 Run を実行した上で Comparison で束ねる。

## 設計原則

| ID | 原則 |
| --- | --- |
| PVD-00001 | provider 固有の知識は Provider Adapter 内に閉じる。上位層 (Run Coordinator) は標準化された推論リクエスト/レスポンスのみを扱う (ARCH-00002) |
| PVD-00002 | provider 追加は契約の追加実装のみで完了する。評価ロジック・結果スキーマには波及しない (NFR-00201) |
| PVD-00003 | provider が返さない計測値は本ツールが推測しない。欠損として扱う (DAT-00104 と整合) |

## 標準化された推論リクエスト

Run Coordinator から Provider Adapter に渡される論理単位です。

| ID | 項目 | 概念 | 必須 |
| --- | --- | --- | --- |
| PVD-00101 | prompt 本体 | Case (DAT-00002) から導出される入力 | 必須 |
| PVD-00102 | 生成条件 | 温度・seed・最大トークン等。Run 単位で固定された値 (DAT-00105) | 任意 (provider が解釈可能な範囲) |
| PVD-00103 | provider 上のモデル参照 | ModelCandidate (DAT-00003) が保持する識別子 | 必須 |
| PVD-00104 | タイムアウト | 上位から渡される打切時間 | 任意 |
| PVD-00105 | リクエストメタ | Run / TaskProfile / Case / Trial の識別子。失敗ログの突合に用いる | 必須 |

## 標準化された推論レスポンス

Provider Adapter が Run Coordinator に返す論理単位です。成功時/失敗時とも本構造に揃えます。

| ID | 項目 | 概念 | 単位 | 必須 |
| --- | --- | --- | --- | --- |
| PVD-00201 | 応答テキスト | provider が返した最終応答の文字列 | — | 成功時必須 |
| PVD-00202 | 応答時間 | リクエスト送信から応答完了までの実時間 | 秒 (浮動小数) | 成功時必須 |
| PVD-00203 | 入力トークン数 | provider が報告する入力側トークン数 | トークン (整数) | provider が返す場合のみ |
| PVD-00204 | 出力トークン数 | provider が報告する生成側トークン数 | トークン (整数) | provider が返す場合のみ |
| PVD-00205 | 生応答 | provider 固有のレスポンスを丸ごと保持する不透明データ | — | 必須 (NFR-00103) |
| PVD-00206 | 失敗種別 | PVD-00301〜 の失敗分類 | — | 失敗時必須 |
| PVD-00207 | 失敗詳細 | 失敗種別を補足する短文と provider 固有エラーコード | — | 失敗時必須 |
| PVD-00208 | provider 識別 | provider 種別と版 / 接続先の概要 (FUN-00306, NFR-00102) | — | 必須 |

注:
- PVD-00203 / PVD-00204 を provider が返さない場合、本ツールは推測せず欠損として記録する。
- PVD-00205 (生応答) は Result Store に保存され、後段の再解釈や障害解析に使われる。

## 失敗種別の分類

Run Coordinator は失敗種別に応じて Trial 失敗 (継続可) と Run 中断 (継続不可) を判定します。

| ID | 失敗種別 | 概念 | 既定の継続性 |
| --- | --- | --- | --- |
| PVD-00301 | provider unreachable | 接続先 provider に到達できない (起動忘れ・ポート違い等) | Run 中断候補 (FLW-00102) |
| PVD-00302 | model not found | provider 上に指定モデルが存在しない | Run 開始前検証で検知することを優先。Run 実行中に検出した場合は Run 中断 (1 Run = 1 Model のため代替モデルへのフォールバックはしない) |
| PVD-00303 | timeout | リクエストが PVD-00104 の打切時間を超えた | Trial 失敗として記録、継続 (FLW-00101) |
| PVD-00304 | malformed response | provider 応答が契約 (PVD-00201〜00205) を満たさない | Trial 失敗として記録、継続 |
| PVD-00305 | provider runtime error | provider 内部エラー (モデルロード失敗・OOM 等) | Trial 失敗として記録、継続 |
| PVD-00306 | unsupported request | 生成条件等を provider が解釈できない | Run 開始前検証で検知することを優先。実行時検出時は Run 中断 |
| PVD-00307 | scoring 適用不可 | 応答テキストが取得できたが scorer の入力前提を満たさない (例: 期待 JSON 形式でない) | Trial 失敗として記録、継続。Quality Scorer (COMP-00006) と協調して判定する |

「Run 中断候補」は最終的な中断判断を Run Coordinator が下す。同一失敗種別が連続する閾値の扱いは v1 では持たず、最初の発生で中断する保守的な方針を既定とする。

## v1 実装上の前提

| ID | 前提 |
| --- | --- |
| PVD-00401 | v1 で実装する Provider Adapter は Ollama (localhost) の 1 種のみ (OOS-00001 と整合) |
| PVD-00402 | provider プロセスの起動・停止・モデル pull は本契約の対象外 (NFR-00303, OOS-00005, OOS-00006) |
| PVD-00403 | streaming・TTFT・decode TPS の計測は本契約に含めない (OOS-00002) |
| PVD-00404 | RAM / GPU メモリの計測は本契約に含めない (OOS-00003) |
| PVD-00405 | Run 中に扱う ModelCandidate は 1 件 (FUN-00207)。Provider Adapter は単一モデル参照を前提に設計され、モデル swap を本ツールから会話しない。モデルを事前ロードして受付するタイプの provider (LM Studio / OpenAI 互換) ともこの前提で適合する |

Ollama 固有のレスポンス形状を契約面に持ち込まない。例えば「特定キー名」「特定エンドポイント形式」は契約に書かず、Adapter 内に閉じ込める。

## 拡張時の影響範囲

| 拡張 | 影響を受ける PVD- |
| --- | --- |
| 新 provider 追加 | 新規 Adapter 実装。本書の契約に追加なし (契約を満たすことを確認) |
| streaming 対応 | PVD-00202 系列に新規 ID を追加し、版識別子 (DAT-00201) を更新 |
| 新失敗種別 | PVD-00308 以降を追加。既存番号の意味は変えない |
| 認証必須 provider 追加 | CFG-00205 / CFG-00504 と協調。本書側は変更不要 |
