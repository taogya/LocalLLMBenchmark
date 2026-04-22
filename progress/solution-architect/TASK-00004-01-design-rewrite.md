# TASK-00004-01 設計大改訂 (1Run=1Model + 周辺整備)

- Status: review-pending
- Role: solution-architect
- Parent: TASK-00004
- Related IDs: REQ-00001..REQ-00009, FUN-001xx..004xx, NFR-00101, NFR-00303, ARCH-00102, ARCH-00203, COMP-00003, COMP-00004, DAT-00003, DAT-00004, FLW-00001, CLI-, CFG-, PVD-, SCR-

## 目的

ユーザー方針確定により、以下の設計改訂を一括で行う。

1. **1 Run = 1 Model への変更** (provider 制御をユーザー責務とする立場と整合)
2. **新エンティティ Comparison の導入** (複数 Run を束ねるランキング成果物)
3. **OOS-00011 の追加** (Copilot CLI / raptor mini 活用検討の独立 ID)
4. **tmp/v0.1.0 参照の除去** (本プロジェクトを初版とする立場で書き直し)
5. **Mermaid 図構文の修正** (`<br/>` → `<br>` + 括弧/矢印整合性点検)

## 設計方針 (改訂後)

### 1 Run = 1 Model

- Run は 1 つの ModelCandidate と 1 つ以上の TaskProfile に対して n 回の Trial を実行する単位とする
- 複数モデル比較は CLI 上で複数 Run を順次実行し、Comparison で束ねる
- provider プロセスのモデル swap は本ツール責務外を維持 (NFR-00303, OOS-00006 と整合)
- 計測公平性: モデル swap 起因の latency 混入を排除

### Comparison (新エンティティ)

- 同一 Task Profile セットに対して実行された複数 Run を束ねる成果物
- 入力: Run 識別子の集合
- 出力: Run 横断のランキング (品質軸 / 速度軸 / 統合軸)
- ランキング算出は Comparison のスコープに移動 (Run のスコープから外す)

## 改訂対象ドキュメントと方針

### 既存 ID の取り扱い

- 意味が変わる既存 ID は本文に `superseded by NEW-ID` を併記
- 新 ID で内容を再定義 (5 桁 0 埋め、単調増加)
- 既存 ID の番号は再利用しない

### 文書ごとの改訂内容

1. **docs/requirements/02-functional.md**
   - FUN-00201 (model 単数化): `superseded by FUN-002xx` (新 ID 採番)
   - FUN-00301/00304 (ランキング = Comparison 成果物): 同様に supersede
   - 新 ID で「Run 開始は 1 ModelCandidate を指定」「Comparison で複数 Run を束ねる」を再定義
   - 必要に応じて Comparison 系の新 FUN- 群を追加 (compare コマンド、軸切替、Run 集合指定)

2. **docs/requirements/04-out-of-scope.md**
   - **OOS-00011** を追加: Copilot CLI (raptor mini 等) 活用の LLM-as-a-Judge
     - 補足: コスト前提 (プレミアムリクエスト x0) と決定的スコアとの併用方針
     - v1.x 以降の検討候補と位置付け
     - 昇格時の前提条件 (`gh copilot` 認証、出力安定性確認、決定的 scorer との併用)
   - OOS-00004 本文に「OOS-00011 を参照」と相互参照を追加

3. **docs/design/01-architecture.md**
   - ARCH-00102 (Orchestration 責務) の「Task × Model × Trial」を「Task × Trial (単一 Model)」に supersede
   - ARCH-00203 (Run 最小単位 = Trial) は維持。Comparison が新たな上位集計単位として加わる旨を追加
   - Mermaid 図の `<br/>` を `<br>` に置換

4. **docs/design/02-components.md**
   - COMP-00003 Run Coordinator: Run = 1 Model を前提に責務を整理 (supersede 必要なら新 ID)
   - COMP-00004 Trial Aggregator: Run 内集計に責務を限定
   - **新 COMP-000XX Run Comparator** を追加: 複数 Run を束ねランキングを算出
   - COMP-00002 Report Renderer: Run 単一表示と Comparison 表示の両方を扱う
   - Mermaid 図の `<br/>` を `<br>` に置換、依存方向の更新

5. **docs/design/03-data-model.md**
   - DAT-00003 ModelCandidate: 変更なし
   - DAT-00004 Run: 「複数 ModelCandidate」→「1 ModelCandidate」に supersede (新 ID で再定義)
   - **新 DAT-000XX Comparison** を追加: 複数 Run を束ねるエンティティ
   - DAT-00007 RunReport: Run 単位レポート (単一モデル) と Comparison レポート (横断) に分離 (supersede 検討)
   - 不変条件・拡張時の影響範囲を更新
   - mermaid classDiagram の `<br/>` を `<br>` に置換 (該当があれば)

6. **docs/design/04-workflows.md**
   - FLW-00001 Run の実行: 複数モデルループを除去し、単一モデル前提に簡素化 (supersede)
   - **新 FLW-000XX Comparison の作成** を追加: ユーザーが Run 識別子集合を指定 → Comparator → Report Renderer
   - mermaid 構文整合性を点検

7. **docs/design/05-cli-surface.md**
   - `run` サブコマンドを単一モデル指定に変更 (supersede 該当 ID)
   - 新サブコマンド `compare` を追加 (Run 識別子集合 → Comparison)
   - 終了コード方針の更新 (Comparison 失敗の分類)

8. **docs/design/06-configuration-sources.md**
   - Run 設定ファイルから model 配列の概念を削除し、単一モデル指定へ supersede
   - Comparison 設定 (Run 識別子集合と軸指定) の扱いを追記

9. **docs/design/07-provider-contract.md**
   - 1 Run = 1 Model 前提を冒頭で明記 (PVD- 群への直接的な supersede は最小限のはず)
   - LM Studio や OpenAI 互換 (ロード前提 provider) との親和性を補足

10. **docs/design/08-scoring-and-ranking.md**
    - Ranking 算出を Comparison スコープに移動 (該当 SCR- を supersede)
    - Run 内集計 (n, mean, p50, p95) は維持
    - Comparison 算出規則 (Run 集合 → モデル別集計 → ランキング) を新 ID で再定義

11. **docs/development/environment.md**
    - tmp/v0.1.0 参照を除去
    - Python 3.13 採用根拠を本プロジェクト視点で書き直し (NFR-00302 標準ライブラリ優先、tomllib 等)

12. **docs/development/release-criteria.md**
    - 1 Run = 1 Model + Comparison 体系で v1.0.0 受入基準を再記述
    - 新 FUN-/CLI- ID への参照に置換

13. **docs/development/traceability.md** および **.github/instructions/traceability.instructions.md**
    - 新規ID接頭辞は不要 (既存カテゴリ内で増番)
    - `superseded by` 運用の例として今回の改訂を簡潔に記載 (任意)

14. **README.md** (※ docs-writer の TASK-00004-02 で対応するためここでは触らない)

## Mermaid 構文点検

- 全 Mermaid ブロックで `<br/>` `<BR/>` を `<br>` に置換
- ノードラベルの括弧バランス、矢印 (`-->` `->>` `--x`) の整合、participant/class の閉じ忘れを目視点検
- 修正記録は task 進捗ログに残す

## 進め方

1. 担当 task の Status を `in-progress` にする
2. 上記 1〜13 を順に改訂 (要件層 → 設計層 → 表面層 → development)
3. 改訂前に対象 ID の波及を洗い出し、進捗ログに記録
4. 既存 ID 意味は変えない。意味変更は新 ID + `superseded by` 併記
5. Mermaid 修正と tmp/v0.1.0 参照除去を漏れなく実施
6. 完了したら Status を `review-pending` に更新

## 完了条件

- 上記 13 ファイルが改訂されている
- 1 Run = 1 Model + Comparison が一貫して反映
- OOS-00011 が独立追加
- tmp/v0.1.0 参照が docs/ 全体から除去
- Mermaid `<br/>` が 0 件
- supersede 元と先の対応が task 本文に列挙されている

## 制約

- 実装に踏み込んだ記述 (クラス名・関数シグネチャ等) を入れない
- 既存設計と矛盾する箇所は supersede で処理し、既存 ID の意味を後付けで変えない

## 進捗ログ

### 改訂ファイル一覧 (絶対パス)

- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/requirements/02-functional.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/requirements/04-out-of-scope.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/01-architecture.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/02-components.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/03-data-model.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/04-workflows.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/05-cli-surface.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/06-configuration-sources.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/07-provider-contract.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/design/08-scoring-and-ranking.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/development/environment.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/development/release-criteria.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/docs/development/traceability.md`
- `/Users/ogasawara/develop/work/LocalLLMBenchmark/.github/instructions/traceability.instructions.md`

### supersede 対応表 (旧 ID → 新 ID)

| 旧 ID | 新 ID | 目的 |
| --- | --- | --- |
| FUN-00201 | FUN-00207 | Run 開始時の対象を「複数 Model」から「1 Model」へ |
| FUN-00301 | FUN-00307 | Run の集計確認をランキング非含有・単一モデル前提に再定義 |
| FUN-00304 | FUN-00308 | ランキング表示の主体を Run から Comparison へ移動 |
| ARCH-00102 | ARCH-00105 | Orchestration 責務を「Task × Trial (単一 Model)」に再定義 |
| COMP-00002 | COMP-00012 | Report Renderer に Comparison 表示責務を加えた再定義 |
| COMP-00003 | COMP-00010 | Run Coordinator を 1 Run = 1 Model 前提に再定義 |
| DAT-00004 | DAT-00008 | Run を「1 ModelCandidate × Task Profile 群 × n」に再定義 |
| DAT-00007 | DAT-00010 | RunReport をランキング非含有・単一モデル前提に再定義 |
| FLW-00001 | FLW-00005 | Run の実行フローから複数 Model ループを除去 |
| CLI-00101 | CLI-00106 | run サブコマンドを 1 Model 指定に変更 |
| CFG-00103 | CFG-00107 | Run 設定から Model 配列を削除し単一参照へ |
| CFG-00203 | CFG-00206 | Run 設定の概念項目を 1 Model 前提に再定義 |
| SCR-00003 | SCR-00802 | ランキング軸を Comparison スコープへ移動 (品質重視) |
| SCR-00601 | SCR-00802 | 品質重視軸を Comparison スコープへ |
| SCR-00602 | SCR-00803 | 速度重視軸を Comparison スコープへ |
| SCR-00603 | SCR-00804 | 統合軸を Comparison スコープへ |
| SCR-00604 | SCR-00805 | 統合スコア算出を Comparison スコープへ |
| SCR-00605 | SCR-00806 | w_quality 既定値を Comparison スコープへ |
| SCR-00606 | SCR-00807 | w_speed 既定値を Comparison スコープへ |
| SCR-00607 | SCR-00808 | 重みのユーザー上書きを Comparison スコープへ |
| SCR-00701 | SCR-00809 | タイブレーカーを Comparison スコープへ |
| SCR-00801 | SCR-00810 | 性能の正規化方針を Comparison スコープへ |

### 採番した新 ID レンジ (カテゴリ別)

| カテゴリ | 新規 ID |
| --- | --- |
| FUN- | FUN-00207, FUN-00307, FUN-00308, FUN-00309, FUN-00310, FUN-00403 |
| OOS- | OOS-00011 |
| ARCH- | ARCH-00105, ARCH-00206, ARCH-00207 |
| COMP- | COMP-00010, COMP-00011, COMP-00012 |
| DAT- | DAT-00008, DAT-00009, DAT-00010, DAT-00011, DAT-00107, DAT-00108, DAT-00109, DAT-00110 |
| FLW- | FLW-00005, FLW-00006 |
| CLI- | CLI-00106, CLI-00107, CLI-00108, CLI-00306 |
| CFG- | CFG-00107, CFG-00108, CFG-00206, CFG-00207, CFG-00506 |
| PVD- | PVD-00405 |
| SCR- | SCR-00802, SCR-00803, SCR-00804, SCR-00805, SCR-00806, SCR-00807, SCR-00808, SCR-00809, SCR-00810 |

### Mermaid 修正件数 / 構文点検結果

- `<br/>` → `<br>` 置換: 10 箇所 (01-architecture.md ×1, 02-components.md ×9)
- 全 mermaid ブロック (docs 配下 9 件 + roles.md 1 件) を再点検
  - ノードラベル `[]` `()` `{}` のバランス: 異常なし
  - 矢印 `-->` `->>` `-->>` `-.->` の整合: 異常なし
  - participant / class の閉じ忘れ: 異常なし
  - リンクラベルのクォート整合: 異常なし
- grep 再確認: docs/ 配下に `<br/>` `<BR/>` 0 件

### tmp/v0.1.0 参照除去

- 改訂前: `docs/development/environment.md` の Python 採用根拠 1 箇所
- 改訂後: 該当除去。本プロジェクト視点 (NFR-00302 標準ライブラリ優先、`tomllib` / `statistics` / 標準型ヒント等) で再記述
- grep 再確認: docs/ 配下に `tmp/v0.1.0` 0 件

### 既存設計との整合性

- Run Coordinator (COMP-00010) が Task Catalog 経由で TaskProfile 群を解決する従来依存を維持
- Run Comparator (COMP-00011) は Result Store のみに依存し、Trial 個別値へ直接アクセスしない (DAT-00106 拡張で担保)
- 認証・provider・scorer 周辺の既存制約 (NFR-00401, NFR-00402, OOS-00006) と整合
- check (CLI-00105) は CFG-00506 の追加で Comparison 設定の参照健全性まで検証範囲を拡張

### 残課題 / リスク

- README ロードマップは TASK-00004-02 (docs-writer) で改訂予定。本 task からは更新せず
- 実装フェーズで CLI サブコマンド名 (`compare` / `comparisons`) の最終確定が残る
- Comparison 結果の永続化レイアウト (Run 結果との同居方法) は実装側コメントで決定する
- partial-failure (CLI-00305) と comparison-incomplete (CLI-00306) の終了コード値 (整数) は実装フェーズで確定
