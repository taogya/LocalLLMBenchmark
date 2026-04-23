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

## 使い方の概観

1. 自分の用途に近い **task profile** を登録する (例: 「メール返信の言い換え」)
2. 比較したい候補モデルを provider 上に用意する (`model pull` または provider CLI で明示取得)
3. **モデルごとに Run を実行する** (1 Run = 1 Model)
4. **Comparison で複数 Run を束ねてランキング表示** し、「あなたの PC・用途における最適モデル」を確認する

## 前提環境

- Python 3.13
- macOS / Linux のいずれか
- Ollama が `http://localhost:11434` で起動済み (`ollama serve` など)。対象モデルは provider CLI で事前に pull 済みでも、後述の `model pull` で明示取得してもよい

## 最短手順

同梱サンプル `configs/` を使い、provider と model の準備から初回 Run → Comparison → Markdown レポートまでを実行する手順です。詳細は [configs/README.md](configs/README.md) を参照。

`--store-root` に渡したディレクトリは自動生成されるため、事前に `mkdir` する必要はありません。以下の例では作業ディレクトリ直下の `./results` を結果保存先として使います。

```sh
# 1. インストール (リポジトリルートで)
pip install -e .

# 2. Ollama を起動
ollama serve &

# 3. provider と model を準備
local-llm-benchmark provider status --config-dir configs
local-llm-benchmark model pull --config-dir configs --model-candidate qwen2.5-7b
local-llm-benchmark model warmup --config-dir configs --model-candidate qwen2.5-7b

# 4. 実行前確認
local-llm-benchmark system-probe --config-dir configs --format markdown
local-llm-benchmark config lint configs
local-llm-benchmark config dry-run configs/run.toml --config-dir configs

# 5. Run を 2 件実行 (生成条件違いを比較するため)
local-llm-benchmark run --config-dir configs --run-config configs/run.toml \
    --store-root ./results
local-llm-benchmark run --config-dir configs --run-config configs/run-alt.toml \
    --store-root ./results

# 6. 2 Run を束ねて Comparison → Markdown レポート
local-llm-benchmark runs --store-root ./results          # Run 識別子を確認
local-llm-benchmark compare --store-root ./results \
    --run-id <RUN_ID_A> --run-id <RUN_ID_B> --axis integrated
local-llm-benchmark report --store-root ./results \
    --comparison-id <COMP_ID> --output ./results/report.md
```

設定だけを短く確認したいときは `config lint`、`run` 直前の確認には `config dry-run` を使います。既存ワークフローの `check --config-dir configs --store-root ./results` も互換面として引き続き利用できます。

`configs/` のサンプル構成・差し替えポイントは [configs/README.md](configs/README.md) に集約しています。

## サブコマンド一覧

CLI 入出力の詳細は [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md) を参照してください。

初回ベンチ前の推奨順は `provider status` -> `model pull` -> `model warmup` -> `system-probe` -> `config lint` -> `config dry-run` -> `run` です。`provider status` / `model pull` / `model warmup` は provider と model の準備、`system-probe` / `config lint` / `config dry-run` は実行前確認を担当します。既存の `check` は互換面として引き続き利用できます。

| サブコマンド | 用途 |
| --- | --- |
| `check` | 既存ワークフロー向けの設定整合性検証。従来の確認手順を保ちたいときに使う |
| `provider status` | provider の起動状態、版情報、利用可能モデル一覧を直接確認 |
| `model pull` | 指定 model を provider に明示取得し、暗黙 pull を避けて準備を進める |
| `model warmup` | 指定 model に最小の実行を 1 回だけ行い、初回 Run 前にロード状態へ寄せる |
| `system-probe` | host 情報、provider 疎通、登録済み候補モデルの可用性を横断確認 |
| `config lint` | 単一設定ファイルまたは `config-dir` を静的に確認し、設定ミスを Run 前に見つける |
| `config dry-run` | `run` 実行前の preflight。provider 到達性や prompt 組立可否を本実行なしで確認 |
| `list` | 登録済み Task Profile / Model Candidate の一覧表示 |
| `run` | 1 Task Profile 群 × 1 Model Candidate × n Trial を実行し Run 識別子を返す |
| `runs` | 過去 Run 一覧表示 |
| `compare` | 複数 Run を束ね、品質軸 / 速度軸 / 統合軸でモデル横断ランキングを返す |
| `comparisons` | 過去 Comparison 一覧表示 |
| `report` | Run 単独サマリ または Comparison ランキングを Markdown / JSON で出力 |

## 既知の制約

- Provider は **Ollama のみ**。LM Studio / OpenAI 互換 API は v1.1 以降の検討対象
- provider プロセスの起動・停止は本ツール責務外。Ollama の起動はユーザー側で行い、model 取得は `model pull` または provider CLI の明示操作で行う (暗黙 pull はしない)
- LLM-as-a-Judge / streaming TTFT / RAM・GPU 計測なし
- Run の途中再開・失敗 Case のみ再実行は未対応
- Comparison 不完全時用の終了コード `EXIT_COMPARISON_INCOMPLETE` (= 6) は **現時点では予約のみ**。`compare` 経路では未消費

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

### v1.1.0 (コンフィグ生成プロンプト)

- `.github/prompts` に対話形式のコンフィグ生成プロンプトを追加 (task profile / provider / run / comparison の TOML をひな形から起こす支援)
- PC スペックと用途を入力するとローカル実行に向く候補モデルの当たりを付けられる model-recommender プロンプトを追加

### v1.2.0 (provider 準備と事前確認 CLI)

- provider の起動状態、版情報、利用可能 model inventory を直接確認する `provider status`
- 1 件の model target を明示取得し、暗黙 pull を行わない `model pull`
- 1 件の model target に最小の provider 実行を 1 回だけ行い、初回 Run 前のロード状態へ寄せる `model warmup`
- 初回ベンチ前に CPU / メモリ / GPU / OS、provider 疎通、候補モデルの可用性を 1 コマンドで確認し、モデル選定の前提をそろえる `system-probe`
- 単一設定ファイルまたは `config-dir` を静的に確認する `config lint`
- `run` 実行前の preflight を本実行なしで行う `config dry-run`
- 既存の `check` は互換面として残し、利用者向けの主導線を `provider status` -> `model pull` -> `model warmup` -> `system-probe` -> `config lint` -> `config dry-run` -> `run` に整理

### v2.0.0 (プロバイダ拡張と高次計測)

- LM Studio / llama.cpp server など Ollama 以外のローカルプロバイダ対応 (Provider Adapter 抽象の再設計を伴う)
- streaming 経由の TTFT / decode TPS 計測
- RAM / GPU メモリの best-effort 計測
- LLM-as-a-Judge を含む高次評価
- チーム共有を前提とした結果ストア
- 将来検討: 過去 run 同士の比較・トレンド表示、BYO-dataset を支援するテンプレートと検証コマンド

ロードマップは要求の変化に応じて見直します。直近の確定スコープは本ファイルとリリースタグを正とします。

## ライセンス

本ソフトウェアは BSD-3-Clause で配布します。著作権者は Taogya です。詳細は [LICENSE](LICENSE) を参照してください。
