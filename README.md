# LocalLLMBenchmark

> あなたの PC で、あなたの用途に最も適したローカル LLM を選ぶための個人向けベンチマークツール

## このツールが解決すること

Web 上には汎用的な LLM ベンチマークが数多く存在しますが、それらは「あなたの PC でどの程度動くか」「あなたの用途に対してどれだけ的確か」には答えません。LocalLLMBenchmark は次の問いに答えることを唯一の目的とします。

> **「私のこの PC、私のこの使い方に対して、ローカルで動くどのモデルが最適か」**

## 想定ユーザー

- ローカルで LLM を試している個人開発者
- 手元の PC スペックを前提にモデル選定をしたい人
- 自分の用途 (要約・分類・抽出など) に近い prompt を持っていて、それで比較したい人

チーム共有や CI 組み込みは v1 のスコープ外です。

## 何を見せるか

- ユーザーが定義した **用途 (task profile)** に対する各モデルの **品質スコア**
- 各モデルの **応答時間とトークン消費**
- 複数 Run を束ねた **Comparison** から導出される **モデルランキング** (品質重視 / 速度重視などの軸を切り替え可能)
- 同一条件で何度実行しても再現する集計値 (複数試行の統計集計を含む)

## 何をしないか

- 汎用 leaderboard の置き換え
- クラウド有料モデルの評価・課金推定
- モデルの自動ダウンロード
- LLM-as-a-Judge による自動採点 (v1 では決定的スコアのみ)
- GPU/RAM 計測 (v2 以降)

## 使い方の概観 (v1)

1. 自分の用途に近い **task profile** を登録する (例: 「メール返信の言い換え」)
2. 比較したい候補モデルを provider 上に用意する (Ollama に pull 済み等)
3. **モデルごとに Run を実行する** (1 Run = 1 Model)
4. **Comparison で複数 Run を束ねてランキング表示** し、「あなたの PC・用途における最適モデル」を確認する

## 前提環境

- Python 3.13
- macOS / Linux のいずれか
- Ollama が `http://localhost:11434` で起動済み (`ollama serve`)、対象モデルが pull 済み

## 最短手順 (v1.0.0)

同梱サンプル `configs/` を使い、初回 Run → Comparison → Markdown レポートまでを実行する手順です。詳細は [configs/README.md](configs/README.md) を参照。

`--store-root` に渡したディレクトリは自動生成されるため、事前に `mkdir` する必要はありません。以下の例では作業ディレクトリ直下の `./results` を結果保存先として使います。

```sh
# 1. インストール (リポジトリルートで)
pip install -e .

# 2. Ollama を起動し、サンプルが参照するモデルを pull
ollama serve &
ollama pull qwen2.5:7b

# 3. 設定整合性を検証
local-llm-benchmark check --config-dir configs --store-root ./results

# 4. Run を 2 件実行 (生成条件違いを比較するため)
local-llm-benchmark run --config-dir configs --run-config configs/run.toml \
    --store-root ./results
local-llm-benchmark run --config-dir configs --run-config configs/run-alt.toml \
    --store-root ./results

# 5. 2 Run を束ねて Comparison → Markdown レポート
local-llm-benchmark runs --store-root ./results          # Run 識別子を確認
local-llm-benchmark compare --store-root ./results \
    --run-id <RUN_ID_A> --run-id <RUN_ID_B> --axis integrated
local-llm-benchmark report --store-root ./results \
    --comparison-id <COMP_ID> --output ./results/report.md
```

`configs/` のサンプル構成・差し替えポイントは [configs/README.md](configs/README.md) に集約しています。

## サブコマンド一覧

CLI 入出力の詳細は [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md) を参照してください。

| サブコマンド | 用途 |
| --- | --- |
| `check` | 設定整合性検証 (期待出力欠落 / 未知 provider 参照等を検出) |
| `list` | 登録済み Task Profile / Model Candidate の一覧表示 |
| `run` | 1 Task Profile 群 × 1 Model Candidate × n Trial を実行し Run 識別子を返す |
| `runs` | 過去 Run 一覧表示 |
| `compare` | 複数 Run を束ね、品質軸 / 速度軸 / 統合軸でモデル横断ランキングを返す |
| `comparisons` | 過去 Comparison 一覧表示 |
| `report` | Run 単独サマリ または Comparison ランキングを Markdown / JSON で出力 |

## 既知の制約 (v1.0.0)

- Provider は **Ollama のみ**。LM Studio / OpenAI 互換 API は v1.1 以降の検討対象
- モデルの自動 download / 起動・停止は本ツール責務外。`ollama pull` / `ollama serve` はユーザー側で実施
- LLM-as-a-Judge / streaming TTFT / RAM・GPU 計測なし
- Run の途中再開・失敗 Case のみ再実行は未対応
- Comparison 不完全時用の終了コード `EXIT_COMPARISON_INCOMPLETE` (= 6) は **v1.0.0 では予約のみ**。`compare` 経路では未消費 (実消費は次バージョン以降)

リリースごとの変更点は [CHANGELOG.md](CHANGELOG.md) を参照してください。

## 関連ドキュメント

設計と要件は `docs/` 配下に分割しています。レビューしやすさを優先し、各文書を短く保ちます。

- [docs/requirements/01-overview.md](docs/requirements/01-overview.md) — 背景・目的・用語
- [docs/requirements/02-functional.md](docs/requirements/02-functional.md) — 機能要件
- [docs/requirements/03-non-functional.md](docs/requirements/03-non-functional.md) — 非機能要件
- [docs/requirements/04-out-of-scope.md](docs/requirements/04-out-of-scope.md) — 非対象スコープ
- [docs/design/01-architecture.md](docs/design/01-architecture.md) — システム全体像
- [docs/design/02-components.md](docs/design/02-components.md) — コンポーネント責務
- [docs/design/03-data-model.md](docs/design/03-data-model.md) — 概念データモデル
- [docs/design/04-workflows.md](docs/design/04-workflows.md) — 主要フロー
- [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md) — CLI 入出力境界
- [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md) — 設定ソースと BYO データ分離
- [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) — provider 抽象契約
- [docs/design/08-scoring-and-ranking.md](docs/design/08-scoring-and-ranking.md) — スコアリングとランキング
- [docs/development/roles.md](docs/development/roles.md) — カスタムエージェントのロール定義
- [docs/development/progress.md](docs/development/progress.md) — 進行管理ルール
- [docs/development/traceability.md](docs/development/traceability.md) — ID 体系とトレーサビリティ
- [docs/development/environment.md](docs/development/environment.md) — 開発環境とツールチェーン
- [docs/development/release-criteria.md](docs/development/release-criteria.md) — リリース受入基準

## ロードマップ

スコープは段階的に拡張します。

### v0.1.0 (設計確定リリース)

- 要件・基本設計の確定 (本リポジトリ初版)
- 開発体制と進行管理ルールの確定
- 実装ゼロ

### v1.0.0 (ミニマル実装リリース)

- 対象 provider: **Ollama のみ**
- 対象計測: **品質スコア + 応答時間 + トークン消費** (provider が返す範囲)
- 同一 case の **複数回実行と統計集計** (n, mean, p50, p95)
- **Comparison によるモデルランキング表示** (品質軸 / 速度軸)
- 結果の **機械可読 (JSON) と人間可読 (Markdown)** の両出力
- セットアップから初回ベンチ完了までを **個人開発者 5 分以内**
- 受入基準の正本は [docs/development/release-criteria.md](docs/development/release-criteria.md)

### v1.1.0 以降 (検討候補)

- 過去 run 同士の比較・トレンド表示
- BYO-dataset を支援するテンプレートと検証コマンド
- LM Studio / OpenAI 互換 API への provider 拡張
- 環境健全性確認コマンド (provider 疎通、モデル可用性)

### v2.0.0 以降 (将来)

- streaming 経由の TTFT / decode TPS 計測
- RAM / GPU メモリの best-effort 計測
- LLM-as-a-Judge を含む高次評価
- チーム共有を前提とした結果ストア

ロードマップは要求の変化に応じて見直します。直近の確定スコープは本ファイルとリリースタグを正とします。

## ライセンス

本ソフトウェアは BSD-3-Clause で配布します。著作権者は Taogya です。詳細は [LICENSE](LICENSE) を参照してください。
