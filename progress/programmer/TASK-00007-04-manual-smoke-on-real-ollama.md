# TASK-00007-04 v1.0.0 manual smoke 実機実行

- Status: done
- Role: programmer
- Parent: TASK-00007
- Related IDs: NFR-00001, NFR-00301, NFR-00303, NFR-00601, NFR-00602, FUN-00207, FUN-00308, REQ-00001

## 目的

Phase 3 (TASK-00007-03) で auto テスト不可と分類された **実機 Ollama を要する manual smoke 5 項目** を実機実行し、実測値を記録する。これにより v1.0.0 リリース判定の最後の論点 (実機未確認) を解消する。

## 実機環境 (ユーザー提示, 2026-04-20)

- Ollama: `ollama serve` 起動中
- モデル: `qwen2.5:7b` pull 済み
- OS: macOS

## 対象 smoke 項目 (release-criteria.md より)

`docs/development/release-criteria.md` 末尾の v1.0.0 smoke 観点チェックリストのうち auto 化できなかった以下 5 項目:

- NFR-00001 初回セットアップから初回 Run 完了までを 5 分以内で実演できる
- NFR-00301 (本文の観察項目を確認)
- NFR-00303 (本文の観察項目を確認)
- NFR-00601 1 Trial あたりオーバーヘッド < 100ms
- NFR-00602 (本文の観察項目を確認)

各項目の本文は `docs/development/release-criteria.md` を参照。

## 実機シナリオ

1. 既存の `configs/` のサンプル (なければ最小サンプル一式を本 task で同梱) を使い、`qwen2.5:7b` で `run` を 1 件実行 (n=3 程度)
2. モデル違い (例: qwen2.5:7b と同モデル設定違い、または同モデルで temperature/seed を変えた 2 Run) で `run` を計 2 件実行し、`compare` → `report` を実行
3. 各実行で経過時間・1 Trial あたりオーバーヘッド・Run/Comparison/Report ファイルの妥当性を計測

サンプル設定が `configs/` に無い場合は本 task でサンプル一式 (TaskProfile 1 件、Provider Ollama 設定、Run 設定、Comparison 設定) を同梱して構わない (Phase 1/2 既存 Loader 仕様の範囲内、設計変更を伴わないこと)。

## 完了条件

- 上記 5 項目すべての実測値が進捗ログに記録されている (達成 / 未達のいずれでも、根拠数値を残す)
- 実機 `run` × 2 → `compare` → `report` が成功する (FUN-00207 / FUN-00308 の実機追認)
- 出力された Run/Comparison/Report ファイルの代表パスを進捗ログに残す
- もし達成できない項目があれば、原因と推奨対応 (設計改訂 / 実装修正 / リリース範囲縮退) を示す
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK (サンプル同梱した場合)
- `python -m unittest discover -s tests` パス

## 制約

- 実装変更は最小限 (サンプル同梱と、smoke 実行で発覚した致命的バグの修正に限る)
- 設計変更が必要なら実装を中断して project-master に報告
- Python 3.13 + stdlib のみ (NFR-00302)
- コメント・docstring・CLI メッセージは日本語

## 報告

- 各 NFR 項目の実測値と達成可否
- 実機実行で使用したコマンド列
- 出力された Run/Comparison/Report のパス
- 同梱したサンプルがあれば一覧
- smoke 実行中に発覚した不具合の有無と対応
- v1.0.0 リリース可否の所見

## 進捗ログ

- 2026-04-20 project-master: 起票 (ユーザー実機環境: ollama serve + qwen2.5:7b)
- 2026-04-20 programmer: 実機 smoke 実行完了 → review-pending。
- 2026-04-20 reviewer: 5 NFR 達成根拠 / 同梱サンプル / OOS- 修正 / 出力ファイル形式 / stdlib / 日本語コメントを確認。`MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 OK、`python -m unittest discover -s tests` 119 OK を再現確認し合格 → done。

  ### 同梱したサンプル一式

  Phase 1/2 既存 Loader を変更せず、CFG- 系既存スキーマに従って `configs/` 配下に最小サンプルを追加した。

  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/README.md](../../configs/README.md) — 利用手順 (短い README)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/task_profiles/qa-basic.toml](../../configs/task_profiles/qa-basic.toml) — TaskProfile 1 件 (CFG-00101, scorer=`normalized_match` SCR-00102, Case 2 件)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/model_candidates.toml](../../configs/model_candidates.toml) — Model Candidate 1 件 (qwen2.5-7b → `qwen2.5:7b`、CFG-00102)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/providers.toml](../../configs/providers.toml) — Ollama (CFG-00104, CFG-00204 既定 localhost)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/run.toml](../../configs/run.toml) — Run 設定 A (temperature=0.0, seed=42, n=3)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/run-alt.toml](../../configs/run-alt.toml) — Run 設定 B (temperature=0.7, seed=123, n=3)
  - [/Users/ogasawara/develop/work/LocalLLMBenchmark/configs/comparison.toml](../../configs/comparison.toml) — Comparison 設定テンプレート (CFG-00207)

  注: 当初 `configs/model_candidates.toml` のコメントに `OOS-00005 / OOS-00006` を含めていたところ `check_oos_no_implementation.py` で FAIL したため、コメントから OOS- 表記を除去 (NFR-00303 のみ参照)。

  ### 実行コマンド列

  ```sh
  # 1. 接続確認
  ollama list                     # qwen2.5:7b のみ存在
  curl -s http://localhost:11434/api/tags

  # 2. 設定検証 (CLI-00105 / FUN-00105)
  local-llm-benchmark check --config-dir configs --store-root tmp/results
  # → "問題なし" / EXIT_SUCCESS

  # 3. 列挙 (CLI-00103 / FUN-00104)
  local-llm-benchmark list --config-dir configs

  # 4. Run A (temperature=0.0)
  /usr/bin/time -p local-llm-benchmark run \
      --config-dir configs --run-config configs/run.toml \
      --store-root tmp/results

  # 5. Run B (temperature=0.7)
  /usr/bin/time -p local-llm-benchmark run \
      --config-dir configs --run-config configs/run-alt.toml \
      --store-root tmp/results

  # 6. 過去 Run 列挙 (CLI-00104 / FUN-00401)
  local-llm-benchmark runs --store-root tmp/results

  # 7. compare (CLI-00107 / FUN-00308)
  local-llm-benchmark compare --store-root tmp/results \
      --run-id run-20260419-163730-qwen2.5-7b \
      --run-id run-20260419-163830-qwen2.5-7b --axis integrated

  # 8. comparisons 列挙 (CLI-00108 / FUN-00403)
  local-llm-benchmark comparisons --store-root tmp/results

  # 9. report (CLI-00102): Run 単独 / Comparison
  local-llm-benchmark report --store-root tmp/results \
      --run-id run-20260419-163730-qwen2.5-7b --output tmp/results/report-runA.md
  local-llm-benchmark report --store-root tmp/results \
      --comparison-id cmp-20260419-163848-n2 --output tmp/results/report-comparison.md

  # 10. 最終検証
  ollama list                     # 差分なし (NFR-00303)
  MMDC_REQUIRED=1 bash scripts/verify.sh
  python -m unittest discover -s tests
  ```

  ### 出力された Run / Comparison / Report のパス

  - Run A: `tmp/results/run-20260419-163730-qwen2.5-7b/` (`meta.json` / `aggregation.json` / `raw/trials.jsonl`)
  - Run B: `tmp/results/run-20260419-163830-qwen2.5-7b/` (同上)
  - Comparison: `tmp/results/comparisons/cmp-20260419-163848-n2/comparison.json`
  - Run A レポート: `tmp/results/report-runA.md`
  - Comparison レポート: `tmp/results/report-comparison.md`
  - 進捗ログ補助: `tmp/results/run-A.json` / `run-B.json` / `compare.json` (CLI 標準出力)、`run-A.stderr` / `run-B.stderr` / `compare.stderr` (進捗 CLI-00203)

  ### NFR 5 項目の実測値と達成可否

  | ID | 観察項目 (release-criteria.md 抜粋) | 実測値 | 達成可否 | 根拠 |
  | --- | --- | --- | --- | --- |
  | NFR-00001 | 初回セットアップ〜初回 Run 完了が 5 分以内 | Ollama 既起動・モデル pull 済の状態から `check` → Run A 完了まで wall ≤ 60 s (Run A 単独で `real 42.17 s`、その他は秒単位) | 達成 | `tmp/results/run-A.stderr` の `real 42.17` と Coordinator 出力 `summary.success_trials=6` |
  | NFR-00301 | macOS / Linux いずれかで全 smoke 観点が通る | macOS 14.x で本 task の全コマンド (check / list / run / runs / compare / comparisons / report) が `EXIT_SUCCESS` 以外を返さず `verify.sh` 全 OK / `unittest` 119 OK | 達成 | 本ログのコマンド列とログ出力 |
  | NFR-00303 | provider 上のモデル download / 起動を本ツールが行わない | Run A/B 実行前後で `ollama list` 出力が完全一致 (`qwen2.5:7b` 1 件のみ、size/digest/modified 不変)。CLI 進捗 (`run-A.stderr` 等) にも pull / start メッセージなし | 達成 | `ollama list` 比較 (本ログ冒頭・末尾) |
  | NFR-00601 | 1 Trial あたりオーバーヘッド < 100 ms | Run A: `real=42.17 s`, sum(elapsed)=42.013 s, n=6 trial → overhead/trial ≈ **26.2 ms**。Run B: `real=3.28 s`, sum(elapsed)=2.890 s, n=6 → overhead/trial ≈ **65.0 ms**。両方とも 100 ms 未満 | 達成 | `tmp/results/run-{A,B}.stderr` と `raw/trials.jsonl` 集計 |
  | NFR-00602 | smoke 規模で結果ディレクトリ容量が常識的範囲 | Run 1 件 = **12 KB** (meta+aggregation+trials.jsonl)、Comparison 1 件 = **4 KB**。10 モデル × 10 TaskProfile × 5 Trial の規模 (= n=50 trial × 100 (case×model) 相当) でも線形外挿で 10 KB × 100 ≒ 1 MB レンジに収まる見込み (生応答 trials.jsonl が支配項) | 達成 | `du -sh tmp/results/run-…` の実測 |

  補足:

  - NFR-00601 は Coordinator が記録する `elapsed_seconds` (provider 応答到達までの実時間) を「provider 呼び出し時間」とみなし、CLI 起動から完了までの `/usr/bin/time -p real` との差分を「ツール内オーバーヘッド」として算出した。CLI 起動時間 (Python import 等) もこの差分に含まれるが、それでも 100 ms/trial 未満で余裕あり。
  - NFR-00001 は「ユーザーが本書手順を 5 分以内に実演できるか」が一次基準。実機 1 Run 自体が 42 s で完走したため、`check` 等を含めても十分 5 分以内に収まる。完全な未経験者の初回セットアップ計測は CI 化の対象外であり、本 smoke の範囲では現実値で達成と判定。
  - NFR-00301 のうち Linux 側は本実機環境では未検証。release-criteria.md は「macOS または Linux いずれか 1 環境」で十分と規定しており、macOS 通過で要件を満たす。

  ### 不具合と対応

  - 不具合 1: `configs/model_candidates.toml` コメントに OOS- ID を引用したことで `check_oos_no_implementation.py` が FAIL。
    - 対応: コメントから `OOS-00005 / OOS-00006` 表記を削除し、`NFR-00303` 参照のみ残した。意味は同等。
    - その後 `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 チェック OK を再確認。
  - 実装本体に対する不具合は発見されなかった。CLI / Coordinator / Comparator / Renderer / Result Store のすべてが Phase 1/2/3 の設計通り動作。

  ### verify.sh / unittest 実行結果

  - `MMDC_REQUIRED=1 bash scripts/verify.sh` → 全 10 チェック OK (`check_id_format` / `check_id_uniqueness` / `check_id_references` / `check_doc_links` / `check_progress_format` / `check_mermaid_syntax` / `check_markdown_syntax` / `check_no_implementation_leak` / `check_role_boundary` / `check_oos_no_implementation`)
  - `python -m unittest discover -s tests` → **Ran 119 tests, OK** (回帰なし)

  ### v1.0.0 リリース可否の所見

  - **可**。NFR-00001 / NFR-00301 / NFR-00303 / NFR-00601 / NFR-00602 のいずれも実機計測で達成。Phase 3 (TASK-00007-03) 時点で auto 化済みの 12 観点と合わせて `docs/development/release-criteria.md` の v1.0.0 smoke チェックリストを全件通過した。
  - 次工程として CHANGELOG / README の v1.0.0 整備に進めて差し支えない。`configs/` サンプル一式が追加済みなので README からはこれを参照する形で「最短手順」セクションを最新化することを推奨 (本 task の対象外、docs-writer に委譲)。
  - 残課題: `EXIT_COMPARISON_INCOMPLETE = 6` (CLI-00306) は v1.0.0 の Comparison 経路で消化されず定数のみ定義の状態 (TASK-00007-03 の reviewer 判断で許容済み)。`tmp/results/` 配下に Phase 1/2 開発中に生成された旧 Run (`openai-compatible-minimal-v1-…`) が `runs` 一覧で `broken: true` として残っているが、これは Phase 1 当時の互換用ダミーであり実機 smoke の判定には影響しない。
