# 04. 主要フロー (Workflows)

ユーザー操作 1 つに対する、コンポーネント間の連携を概念レベルで示します。シーケンス図はあくまで責務の流れを示すもので、実装シグネチャを規定しません。

## フロー一覧

| ID | フロー | トリガ |
| --- | --- | --- |
| FLW-00001 | (superseded by FLW-00005) Run の実行 | ユーザーが対象を指定して開始 |
| FLW-00002 | 結果の確認 | ユーザーが Run 識別子を指定 |
| FLW-00003 | 登録内容の整合性確認 | ユーザーが明示的に確認を要求 |
| FLW-00004 | 過去 Run の一覧確認 | ユーザーが一覧を要求 |
| FLW-00005 | Run の実行 (1 Run = 1 Model) | ユーザーが 1 Model + Task Profile 群を指定して開始 |
| FLW-00006 | Comparison の作成 | ユーザーが Run 識別子集合を指定 |

## FLW-00001 (superseded by FLW-00005) Run の実行

複数 ModelCandidate をループで回す代フローとして記述していた。1 Run = 1 Model 方針 (FUN-00207, ARCH-00207) に伴い FLW-00005 で再定義した。複数モデル比較は FLW-00006 (Comparison の作成) と組み合わせる。

## FLW-00005 Run の実行 (1 Run = 1 Model)

関連: FUN-00207, FUN-00202, FUN-00204, FUN-00205, FUN-00206, NFR-00501, NFR-00502

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Cat as Task Catalog
    participant Coord as Run Coordinator
    participant Adapter as Provider Adapter
    participant Scorer as Quality Scorer
    participant Agg as Trial Aggregator
    participant Store as Result Store

    User->>CLI: run (Task Profile 群 / 1 Model / n)
    CLI->>Cfg: 設定読込
    Cfg->>Cat: Task Profile 解決
    Cfg-->>CLI: 構成済みコンテキスト
    CLI->>Coord: Run 開始
    Coord->>Store: Run 受付 (進行中)
    loop 各 Trial (Task × n)
        Coord->>Adapter: 推論要求
        Adapter-->>Coord: 推論結果 / 失敗
        Coord->>Scorer: 採点要求 (成功時のみ)
        Scorer-->>Coord: スコア
        Coord->>Store: Trial 保存
        Coord->>User: 進捗通知
    end
    Coord->>Agg: 統計集計要求
    Agg-->>Coord: Case / Run 集計 (単一モデル)
    Coord->>Store: 集計値保存 (完了)
    Coord-->>CLI: Run サマリ
    CLI-->>User: Run 完了通知 (Run 識別子)
```

注:
- Run は 1 ModelCandidate に限定される。複数モデルを比較したい場合は、ユーザーが provider 上でモデルを入れ替えて複数回 Run を実行し、その後 FLW-00006 で束ねる。
- 個別 Trial の失敗は Run 全体を停止させない (FUN-00204)。
- 進捗通知の媒体は実装フェーズで決定する。

## FLW-00006 Comparison の作成

関連: FUN-00308, FUN-00309, FUN-00310, ARCH-00206, NFR-00201

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Store as Result Store
    participant Comparator as Run Comparator
    participant Report as Report Renderer

    User->>CLI: compare (Run 識別子集合 / ランキング軸)
    CLI->>Store: 各 Run の集計値 / モデルサマリ取得
    Store-->>CLI: 集計値集合
    CLI->>Comparator: Comparison 作成要求
    Comparator->>Comparator: Run 数下限検査 (DAT-00108 / DAT-00109)
    Comparator->>Comparator: TaskProfile セット一致検査 (DAT-00109)
    Comparator->>Comparator: モデル横断ランキング算出
    Comparator->>Store: Comparison 保存
    Comparator-->>CLI: Comparison 識別子
    CLI->>Report: Comparison レンダリング要求
    Report-->>CLI: 人間可読 / 機械可読
    CLI-->>User: ランキング表示 / 出力
```

注:
- 指定された Run 集合が 2 件未満の場合、Run Comparator は Comparison を生成せず、エラーをユーザーに返す (DAT-00108 / DAT-00109)。
- TaskProfile セットが不一致な Run 集合を指定された場合、Run Comparator は Comparison を生成せず、不一致をユーザーに返す。
- ランキング軸の指定がない場合、Comparison の既定軸 (CFG-00207) を用いる。

## FLW-00002 結果の確認

関連: FUN-00307, FUN-00302, FUN-00303, FUN-00305, NFR-00004

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Store as Result Store
    participant Report as Report Renderer

    User->>CLI: report (Run 識別子)
    CLI->>Store: Run 集計値取得
    Store-->>CLI: 集計値 (単一モデル)
    CLI->>Report: レンダリング要求
    Report-->>CLI: 人間可読 / 機械可読
    CLI-->>User: 表示 / 出力
```

ランキング表示は本フローの対象外とし、Comparison を作成する FLW-00006 で表示する。

## FLW-00003 登録内容の整合性確認

関連: FUN-00105, FUN-00402

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Cat as Task Catalog

    User->>CLI: 確認要求
    CLI->>Cfg: 設定読込
    Cfg->>Cat: Task Profile 整合性検証
    Cat-->>Cfg: 検証結果
    Cfg-->>CLI: 集約結果
    CLI-->>User: 検出された問題一覧 (なければ空)
```

検証内容の例 (実装で詳細化):
- 参照される provider 種別が登録済みか
- TaskProfile が必須要素 (Case / 評価契約) を満たしているか
- 認証情報が必要な provider に対して、対応する環境変数が解決可能か

## FLW-00004 過去 Run の一覧確認

関連: FUN-00401

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Store as Result Store

    User->>CLI: 一覧要求
    CLI->>Store: Run メタ情報走査
    Store-->>CLI: Run 識別子と要約
    CLI-->>User: 一覧表示
```

## エラー処理の方針

| ID | 方針 |
| --- | --- |
| FLW-00101 | 復旧可能なエラー (個別 Trial の失敗等) は記録して継続する |
| FLW-00102 | 復旧不可能なエラー (設定不整合、Result Store 書込不可等) は Run 開始前に検知して中断する |
| FLW-00103 | Run 中の中断時、書込済み Trial は失われない。集計値は欠損として処理される |
