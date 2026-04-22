# Local LLM Benchmark
ローカルLLMベンチマークツール

## 現在地

request 00004 で config 外部化の最小スコープを実装しました。共通 CLI は provider 固有コマンドを持たず、`configs/` の benchmark suite、model registry、prompt set、provider profile と、sibling の `prompts/` を読んで実行します。

初期 sample suite は `tier:entry`、`tier:balanced`、`tier:quality` の 3 モデルを TOML で固定し、generic CLI からそのまま比較できる状態です。

provider 拡張の最小スライスとして `openai_compatible` adapter も追加し、OpenAI-compatible local server を provider profile で接続できるようにしました。既定 suite は引き続き Ollama sample のままです。

## 最小実行

```bash
# インストール
python -m pip install -e .
# benchmark suite の一覧を表示
local-llm-benchmark suites --config-root configs
# 指定した benchmark suite の詳細と準備対象を確認
local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs
# benchmark suite を実行
local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1
# 保存済み run の metric 要約を表示
local-llm-benchmark report --run-dir tmp/results/<run_id>
# 保存済み run を baseline 差分で比較
local-llm-benchmark compare --run-dir tmp/results/<run_a> --run-dir tmp/results/<run_b>
```

`--config-root` は `benchmark_suites`、`model_registry`、`prompt_sets`、`provider_profiles` を読むルートです。sample 構成では sibling の `prompts/` も自動で解決します。

`run` 完了後は出力された `result_dir` を `report --run-dir` に渡すと、single-run の metric 要約を確認できます。表示上の `records` は manifest の `record_count`、各 metric 行の `n` は `sample_count` で、実行失敗や auto 評価対象外 record があると一致しない場合があります。

`compare` は先頭の `--run-dir` を baseline にし、`model_key | prompt_category | prompt_id | metric_name` ごとの差分だけを既定表示します。同一 row は header の `identical_rows_omitted` へ集約し、`missing` は run error、auto 評価対象外、suite / plan 差分などで row が存在しないことを表します。

`compare` の `json_valid_rate`、`format_valid_rate`、`constraint_pass_rate` などは strict machine-readable JSON と lexical / structural contract-following の差分です。`json_payload_valid_rate`、`payload_exact_match_rate`、`payload_format_valid_rate`、`payload_constraint_pass_rate` は、前後空白除去とレスポンス全体が単一 fenced block のときだけ wrapper を外した payload diagnostic です。payload 系は strict fail を上書きせず、semantic quality や自然な rewrite 品質を直接表すものでもありません。

## Readiness の見方

`code readiness` と `environment readiness` を分けると、失敗箇所を切り分けやすくなります。

- code readiness: `local-llm-benchmark suites --config-root configs` と `local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs` が通り、config と CLI が読めることを確認します。
- environment readiness: local server を起動し、必要な model identifier を準備し、認証が必要なら環境変数を export したうえで `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1` が通ることを確認します。

README 記載の `suites` -> `run` を実環境でまとめて確認したい場合は、Ollama 起動済みかつ sample suite の 3 モデル取得済みの前提で次を実行します。

```bash
LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE=1 python -m unittest tests.cli.test_live_smoke
```

## モデル取得の前提

モデル取得は provider ごとの責務です。このパッケージはモデルの自動ダウンロードや自動 pull を行いません。benchmark 実行前に、使う provider の CLI や管理手段で必要モデルを事前取得してください。

sample suite をそのまま使う場合も、`configs/model_registry/local-models-v1.toml` にあるモデルがローカルで利用可能である前提です。現在同梱している sample config は Ollama profile を使うため、実行前に次のような取得が必要です。

```bash
ollama pull gemma3:latest
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
```

他の provider を使う場合も考え方は同じで、このパッケージではなく provider 側の手段でモデルを準備します。

OpenAI-compatible local server を使う場合は、model registry 側で `provider_id = "openai_compatible"` の model を定義し、`provider_model_name` を server 側で利用可能な model identifier に合わせます。LM Studio では通常、`lms ls` に出る actual downloaded model key を基準に読むのが自然です。接続先は `configs/provider_profiles/openai-compatible-local.toml` をベースに切り替えます。

sample profile は keyless server を既定にしており、`api_key_env` を省略すると Authorization header を送りません。認証が必要な場合だけ `connection.api_key_env = "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY"` のように環境変数名を指定し、値そのものは `export LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY=...` のように環境変数で渡してください。設定ファイルに平文 `api_key` は置かない前提です。

LM Studio を使う場合の最短手順は `docs/lmstudio/README.md` にまとめています。LM Studio は `lms ls` に出る actual downloaded model key を基準に読むのが自然で、repo 同梱の `llmb-minimal-chat` は `openai-compatible-minimal-v1` をそのまま試すための readiness alias slot です。Ollama の既定導線はそのままにしつつ、OpenAI-compatible readiness だけを試したい場合は server 側で `<downloaded_model_key>` に `--identifier llmb-minimal-chat` を付けて load したうえで次を実行してください。

```bash
local-llm-benchmark suites openai-compatible-minimal-v1 --config-root configs
local-llm-benchmark run --config-root configs --suite openai-compatible-minimal-v1
```

`openai-compatible-minimal-v1` は readiness 用の最小 suite であり、正式比較用 suite ではありません。

## ロード運用の前提

benchmark core と runner は逐次実行で、model の自動 download、load、pin、unload を行いません。Ollama は provider profile の `keep_alive` を request ごとに送る前提で、同梱の `local-default.toml` は baseline 向けに `keep_alive = "5m"` を置いています。LM Studio は OpenAI-compatible endpoint の JIT loading、Idle TTL、Auto-Evict の既定動作を読む前提で、actual downloaded model key が自然な基準です。`llmb-minimal-chat` alias と `openai-compatible-minimal-v1` は repo 同梱 readiness slot の互換導線として扱います。

## Config 構成

```text
configs/
	benchmark_suites/
	model_registry/
	prompt_sets/
	provider_profiles/
prompts/
	classification/
	constrained_generation/
	extraction/
	rewrite/
	short_qa/
	summarization/
```

## 初期評価指標

初期固定版として扱うのは deterministic scorer に基づく指標です。manual または hybrid が必要な quality scorer は、結果保存の対象外ではなくても、現時点では公式 pass/fail に使いません。

| カテゴリ | 初期固定の主指標 | 何が分かるか |
| --- | --- | --- |
| classification | accuracy, macro_f1 | 全体の当たり率と、少数ラベルも含めて偏りなく分類できるかが分かる。 |
| extraction | exact_match_rate, json_valid_rate, json_payload_valid_rate, payload_exact_match_rate | strict の raw JSON gate と、最小 unwrap 後の payload correctness を分けて読める。 |
| rewrite | constraint_pass_rate | 明示した制約を守って出力できるかが分かる。 |
| summarization | length_compliance_rate | 指定した文字数レンジを守れるかが分かる。 |
| short_qa | exact_match_rate | 短い質問に対して正答文を返せるかが分かる。 |
| constrained_generation | constraint_pass_rate, format_valid_rate, payload_format_valid_rate, payload_constraint_pass_rate | strict の制約・形式 gate と、最小 unwrap 後の payload 妥当性を分けて読める。 |

現時点で固定している scorer は `exact_match_label v1`、`exact_match_text v1`、`exact_match_json_fields v1`、`json_valid v1`、`format_valid v1`、`constraint_pass v1`、`length_compliance v1` です。sample prompt もこの定義にそろえてあります。

特に `json_valid_rate` と `format_valid_rate` は downstream へそのまま流せるかを見る運用 gate として扱います。初期固定の閾値は `json_valid_rate >= 1.0` と `format_valid_rate >= 1.0` で、それ以外の run 閾値は dataset 較正前のため未固定です。

一方、`json_payload_valid_rate`、`payload_exact_match_rate`、`payload_format_valid_rate`、`payload_constraint_pass_rate` は、前後空白除去とレスポンス全体が単一 fenced block のときだけ wrapper を外した後の diagnostic です。先頭末尾 prose の切り落としや壊れた JSON 修復は行わず、strict fail を上書きしません。

読み解き例:

- classification で accuracy が近くても macro_f1 に差があれば、少数クラスへの強さに差がある。
- extraction で exact_match_rate が高くても json_valid_rate が 1.0 を切るなら、自動処理に流し込みにくい。
- rewrite で constraint_pass_rate が低ければ、自然さ以前に出力制約の遵守が不安定である。

## 現行評価方式の補足

現行の公式評価は、request snapshot に保存した evaluation.conditions のうち、`evaluation_mode = auto` の項目だけを deterministic scorer で採点する形です。`case-evaluations.jsonl` は 1 case x 1 metric、`run-metrics.json` は model_key x prompt_id x prompt_category 単位の集計値を持ちます。

現時点で公式 auto 評価に含めないものは、レーベンシュタイン距離、文字列類似度、ROUGE-like、embedding 類似度、LLM judge、manual / hybrid の quality scorer です。これらは比較候補としては残していますが、現在の `case-evaluations.jsonl` と `run-metrics.json` には混在させません。

注意点として、`json_valid_rate` は raw response の JSON parse 成功だけを見る指標です。required_fields の一致や値の正確性は `exact_match_rate` または `payload_exact_match_rate`、JSON object の key や型の妥当性は `format_valid_rate` または `payload_format_valid_rate` と合わせて読む必要があります。

## ランダム性への現状対応

- sample baseline suite は `temperature = 0.0`、`top_p = 0.95`、`seed = 7` を上書きし、request snapshot に generation 条件を保存します。
- scorer 自体は deterministic ですが、LLM 応答の揺れを統計的に吸収する仕組みはまだありません。同一 case の複数回実行、分散集計、自己一致投票、信頼区間、judge による再採点は未対応です。
- `seed` の実効性は provider 依存です。Ollama は request に `seed` を送りますが、OpenAI-compatible v1 は `seed` を payload に含めません。
- そのため現在の仕組みで確認しやすいのは、正解や制約が機械可読で、単一出力に寄せやすい task の完走性、形式妥当性、制約遵守です。意味保持、要約品質、言い換え許容、run 間の揺れ幅そのものはまだ確認できません。

## ロードマップ

1. config 外部化: 実装済み。benchmark suite、model registry、prompt set、provider profile を設定ファイルから切り替えられるようにした。
2. 結果保存: 実装済み。既定で `tmp/results/<run_id>/` に `manifest.json`、`records.jsonl`、`case-evaluations.jsonl`、`run-metrics.json`、`raw/` を保存し、raw response と正規化済み記録を分離して残す。
3. 評価データ整備: 最小スライス実装済み。6 カテゴリ各 1 prompt、evaluation_reference、deterministic scorer に基づく case 単位評価と run 集計をそろえた。
4. provider 拡張: 着手済み。Ollama に加えて `openai_compatible` provider の最小スライスを追加し、non-streaming の chat completions API を provider profile 経由で利用できるようにした。
5. 比較レポート整備: 最小スライス実装済み。`compare --run-dir ...` で保存済み結果を baseline 差分として表示し、既定では differing rows のみを確認できるようにした。
