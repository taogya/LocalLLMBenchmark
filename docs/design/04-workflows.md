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
| FLW-00007 | 実行環境と provider 可用性の確認 | ユーザーが `system-probe` を要求 |
| FLW-00008 | 設定ソースの静的検証 | ユーザーが `config lint` を要求 |
| FLW-00009 | Run 設定の dry-run 事前確認 | ユーザーが `config dry-run` を要求 |
| FLW-00010 | provider の起動状態と inventory 確認 | ユーザーが `provider status` を要求 |
| FLW-00011 | model の pull | ユーザーが `model pull` を要求 |
| FLW-00012 | model の warmup | ユーザーが `model warmup` を要求 |

provider 側準備を含む主導線は `provider status` → `model pull` → `model warmup` → `system-probe` → `config lint` → `config dry-run` → `run` とする。既に provider と model が整っている場合は先頭 3 ステップを省略できる。`check` は既存互換の静的確認面として残す。

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
- 進捗通知の具体媒体は本書の対象外とする。

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

注:
- 本フローは静的検証に限定し、provider 通信と host hardware 収集は行わない。
- 本フローに含める検証は、登録内容と参照整合性の確認に限る。

本フローに含まれる検証:
- 参照される provider 種別が登録済みか
- TaskProfile が必須要素 (Case / 評価契約) を満たしているか
- 認証情報が必要な provider に対して、対応する環境変数が解決可能か
- `check` は既存互換面として本フローを維持する。利用者向け主導線の静的確認は FLW-00008 (`config lint`) を優先する。

## FLW-00008 設定ソースの静的検証

関連: FUN-00105, FUN-00402, FUN-00406

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Cat as Task Catalog

    User->>CLI: config lint (単一設定ファイル / 設定ディレクトリ)
    CLI->>Cfg: 主入力と補助設定ソース読込
    Cfg->>Cat: 必要時の Task Profile 解決
    Cat-->>Cfg: 解決結果
    Cfg-->>CLI: 検証結果
    CLI-->>User: 問題一覧または問題なし
```

注:
- 単一ファイル入力でも、相互参照を持つ場合は必要最小限の補助設定ソースだけを解決する。
- provider 通信、host facts 収集、prompt 組立は本フローに含めない。
- `comparison.toml` を検証する場合は Result Store 側の Run 実在確認を静的整合性確認として扱う。

## FLW-00007 実行環境と provider 可用性の確認

関連: FUN-00404, FUN-00405, NFR-00002, NFR-00301, NFR-00302

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Host as Local System
    participant Cfg as Configuration Loader
    participant Adapter as Provider Adapter

    User->>CLI: system-probe
    CLI->>Host: OS / CPU / メモリ / GPU 取得
    Host-->>CLI: Host facts / unknown
    CLI->>Cfg: Provider / Model Candidate 読込
    Cfg-->>CLI: Probe 対象一覧
    loop 各 provider / model ref
        CLI->>Adapter: 到達確認 / model ref 解決
        Adapter-->>CLI: 到達結果 / 解決結果 / 生応答
    end
    CLI-->>User: JSON / Markdown スナップショット
```

注:
- `system-probe` は CFG-00102 / CFG-00104 を入力にし、TaskProfile / Run / Comparison は読まない。
- host facts は best-effort で取得し、取得不能項目は `unknown` として表現する。これだけでは probe 全体の失敗にしない。
- Run 設定や TaskProfile を読んだ prompt 組立は本フローに含めない。
- `provider status` は別フロー (FLW-00010) とし、本フローは host facts と登録済み Model Candidate の横断観測に集中する。
- `config dry-run` は別フロー (FLW-00009) とし、本フローは host facts と provider / model の横断観測に集中する。

## FLW-00009 Run 設定の dry-run 事前確認

関連: FUN-00407, NFR-00002, NFR-00302

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Cat as Task Catalog
    participant Adapter as Provider Adapter

    User->>CLI: config dry-run (Run 設定)
    CLI->>Cfg: Run 設定と補助設定ソース読込
    Cfg->>Cat: Task Profile / 代表 Case 解決
    Cat-->>Cfg: 実行順に基づく代表 Case
    Cfg-->>CLI: 構成済み preflight コンテキスト
    CLI->>Adapter: provider 到達確認 / 指定 model ref 解決
    Adapter-->>CLI: probe 結果
    CLI->>CLI: 代表 1 Case の prompt 組立
    CLI-->>User: JSON / Markdown preflight サマリ
```

注:
- 主入力は Run 設定であり、host facts 収集や全 Model Candidate 走査は行わない。
- prompt 組立は Run で実際に使う順序から決まる代表 1 Case のみを対象とし、実推論・採点・Result Store 書込は行わない。
- `system-probe` を置き換えるものではなく、Run 実行前の個別 preflight 面として位置づける。
- `model warmup` は別フロー (FLW-00012) とし、本フローでは provider 実行を伴うロード操作を行わない。

## FLW-00010 provider の起動状態と inventory 確認

関連: FUN-00408, NFR-00002, NFR-00302

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Adapter as Provider Adapter

    User->>CLI: provider status
    CLI->>Cfg: Provider 接続情報読込
    Cfg-->>CLI: Provider 一覧
    loop 各 provider
        CLI->>Adapter: status snapshot 要求
        Adapter-->>CLI: 到達状態 / 版情報 / 利用可能 model inventory
    end
    CLI-->>User: JSON / Markdown status
```

注:
- host facts、Model Candidate との照合、TaskProfile / Run 読込は本フローに含めない。
- `system-probe` は登録済み Model Candidate と host snapshot の横断観測、`provider status` は provider inventory の直接確認に責務を分ける。

## FLW-00011 model の pull

関連: FUN-00409, NFR-00002, NFR-00302

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Adapter as Provider Adapter

    User->>CLI: model pull
    CLI->>Cfg: Provider / model target 解決
    Cfg-->>CLI: pull 対象
    CLI->>Adapter: model pull 要求
    loop provider が進捗を返す間
        Adapter-->>CLI: pull 進捗
        CLI-->>User: 進捗表示 (stderr)
    end
    Adapter-->>CLI: pull 完了 / 失敗
    CLI-->>User: JSON / Markdown summary
```

注:
- TaskProfile / Run / host facts は読まない。
- `run` / `system-probe` / `config dry-run` / `model warmup` は本フローを暗黙起動しない。

## FLW-00012 model の warmup

関連: FUN-00410, NFR-00002, NFR-00302

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Entry
    participant Cfg as Configuration Loader
    participant Adapter as Provider Adapter

    User->>CLI: model warmup
    CLI->>Cfg: Provider / model target 解決
    Cfg-->>CLI: warmup 対象
    CLI->>Adapter: minimal warmup 要求
    CLI-->>User: 開始通知 (stderr)
    Adapter-->>CLI: ready / failed と経過時間
    CLI-->>User: 完了通知 (stderr) と JSON / Markdown summary
```

注:
- `config dry-run` と異なり、実際の provider 実行を 1 回行う。
- TaskProfile / Run 設定由来の prompt 組立、採点、Result Store 書込は行わない。

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
