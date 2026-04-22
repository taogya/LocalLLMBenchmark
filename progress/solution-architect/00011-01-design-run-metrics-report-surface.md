---
request_id: "00011"
task_id: "00011-01"
parent_task_id: "00011-00"
owner: "solution-architect"
title: "design-run-metrics-report-surface"
status: "done"
depends_on: []
created_at: "2026-04-18T15:15:00+09:00"
updated_at: "2026-04-18T16:35:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture/benchmark-foundation.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/benchmark/evaluation.py"
  - "src/local_llm_benchmark/benchmark/runner.py"
  - "src/local_llm_benchmark/storage/jsonl.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_live_smoke.py"
  - "progress/reviewer/00009-05-review-roadmap-3-minimum-slice.md"
---

# 入力要件

- run-metrics の利用面を report 準備として固めたい。
- progress/solution-architect/00011-01-design-run-metrics-report-surface.md を done まで進めたい。
- 比較レポート本体の前段として、run directory を受けて run-metrics を stable に読める最小 CLI / 表示仕様を決めたい。

# 整理した要件

- provider 固有語を増やさず、JSON artifact schema を大きく変えない前提で、最小の user-facing 導線を決める。
- 情報過多を避けつつ、metric と sample_count と scope の意味が見える一覧表示を決める。
- run-metrics の value / threshold / sample_count / passed の見せ方と、manifest.record_count との差分の扱いを固定する。
- README、architecture docs、CLI tests で何を固定するかを整理し、比較レポート本体へ接続しやすい入口にする。

# 作業内容

- README.md、docs/architecture/benchmark-foundation.md、src/local_llm_benchmark/cli/main.py、src/local_llm_benchmark/storage/jsonl.py、tests/cli/test_main.py、tests/cli/test_live_smoke.py、progress/reviewer/00009-05-review-roadmap-3-minimum-slice.md を確認し、現状の CLI は run と suites のみで、run-metrics は artifact 保存止まりであることを確認した。
- src/local_llm_benchmark/benchmark/evaluation.py と src/local_llm_benchmark/benchmark/runner.py を確認し、run-metrics.json の scope が model_key x prompt_id x prompt_category、sample_count が metric ごとの scored case 数、passed が threshold 未評価時に null を取りうることを確認した。
- progress/project-master/00011-00-run-metrics-usage-surface.md、progress/programmer/00011-02-implement-run-metrics-report-surface.md、progress/reviewer/00011-03-review-run-metrics-report-surface.md を確認し、今回の子タスクが single-run の最小 report 入口を定義する役割であることを整理した。
- request 00009 の reviewer 記録を参照し、次段階では CLI 経路で metric 名、scope、sample_count を固定すると配線崩れを早く検知できるという前提を引き継いだ。

# 判断

- 最小で自然な CLI は report とし、形は local-llm-benchmark report --run-dir <run_dir> を推奨する。metrics は内部 artifact 名をそのまま露出しやすく、後続の比較レポート本体へつながる user-facing 名としては弱い。
- 引数は positional ではなく required な --run-dir を使う。既存 CLI が required option を中心にしていることと、将来 multi-run 比較へ広げるときにオプション追加で拡張しやすいことを優先する。
- report CLI は run_dir 配下の manifest.json と run-metrics.json を読む。suite_id と record_count の表示、および sample_count の意味差の説明に manifest が必要なためである。
- 一覧表示の最小項目は scope.model_key、scope.prompt_category、scope.prompt_id、metric_name、value、threshold、passed、sample_count とする。scorer_name、scorer_version、aggregation は JSON 側に残し、既定表示からは外して情報量を抑える。
- value は集計値として固定小数 3 桁表示を基本とする。sample_count は n=<count> で短く見せ、legend で n が sample_count だと明示する。
- threshold は人が読める文字列へ整形する。null は -、min は >=<value>、range は <min>-<max> <unit> とする。range threshold は現在の run passed 判定対象ではないため、threshold を表示しつつ passed は n/a とする。
- passed は true を pass、false を fail、null を n/a と表示する。null は失敗ではなく、run gate が未固定または run 集計では未評価であることを表す。
- manifest.record_count と sample_count は同じ意味ではないため、等値比較を前提にしない。record_count は run 全体の試行件数、sample_count は各 metric 行に寄与した case 数である。
- report CLI は header で record_count を 1 回だけ表示し、各行で n=sample_count を表示する。加えて、metrics 内の unique scope 数と manifest.record_count が一致しない場合だけ informational note を 1 行出し、実行失敗または auto 評価対象外 record がある可能性を説明する。
- docs と tests では command 名、required option、一覧の最小列、threshold / passed の整形、record_count と sample_count の意味差、missing artifact 時の error を固定する。
- 比較レポート本体へは、single-run の report が読む artifact loader と row 正規化を再利用する形でつなぐ。今回の段階では比較機能そのものは入れず、single-run summary を stable な入口として固定する。

# 成果

## 推奨 CLI 形状

- 推奨コマンドは local-llm-benchmark report --run-dir <run_dir>。
- report は「保存済み run の結果を読む user-facing 入口」を表し、内部 artifact 名の run-metrics にコマンド名を縛られない。
- 既定ではテキスト要約だけを出し、filter、sort option、JSON 再出力、複数 run 集計は入れない。
- report は run_dir 配下の manifest.json と run-metrics.json を前提とし、どちらかが欠ける場合は exit code 1 で明示的に失敗させる。

## 表示例

```text
run_id: cli-test-run
suite_id: local-three-tier-baseline-v1
run_dir: tmp/results/cli-test-run
records: 18
metric_rows: 27
legend: scope=model_key | prompt_category | prompt_id, n=sample_count, passed=n/a when run threshold is not evaluated
- local.entry.gemma3 | classification | contact-routing-v1 | accuracy | value=1.000 | threshold=- | passed=n/a | n=1
- local.entry.gemma3 | extraction | invoice-fields-v1 | json_valid_rate | value=1.000 | threshold=>=1.0 | passed=pass | n=1
- local.entry.gemma3 | summarization | meeting-notice-summary-v1 | length_compliance_rate | value=1.000 | threshold=80-120 chars | passed=n/a | n=1
note: manifest.record_count=18, metric scopes=17. sample_count は各 metric 行に寄与した case 数で、実行失敗または auto 評価対象外 record は含まない。
```

補足:

- note 行は unique scope 数と manifest.record_count が一致しない場合だけ表示する。
- row の並び順は model_key、prompt_id、metric_name の安定ソートを基本にする。
- prompt_category は scope の意味を見せるために残し、provider_id は共通 CLI に持ち込まない。

## 最小実装方針

- src/local_llm_benchmark/cli/main.py に report subcommand を追加し、handler から専用 renderer を呼ぶ。
- report の読み出しと整形は main.py に直書きせず、cli 配下の小さな helper module へ分ける。責務は「manifest と run-metrics を読む」「最小検証をする」「テキスト要約へ整形する」までに留める。
- helper は manifest.json から run_id、suite_id、record_count を取り、run-metrics.json から metrics 配列を取り出す。schema_version の厳密検証は最小に留め、必要キー欠落だけ error にする。
- row renderer は次を担当する。
  - value の 3 桁整形
  - threshold の null / min / range 整形
  - passed の pass / fail / n/a 整形
  - n=sample_count の短縮表示
  - unique scope 数と record_count の比較から note 行を条件付き追加
- storage の JSON artifact schema は変えない。run-metrics.json へ列追加はせず、既存 manifest と run-metrics の読み合わせだけで利用面を作る。
- 比較レポート本体で再利用しやすいよう、artifact 読み出しと row 整形は report handler から分けておくが、新しい reporting 層までは増やさない。

## テスト観点

- tests/cli/test_main.py に report help の確認を追加し、run、suites、report が並ぶこと、--run-dir が必須であることを固定する。
- tests/cli/test_main.py に synthetic run_dir を使う report 成功 test を追加し、run_id、suite_id、records、legend、scope、metric_name、value、threshold、passed、n が表示されることを確認する。
- threshold 整形は少なくとも 3 パターンを固定する。threshold null は -、min は >=1.0、range は 80-120 chars のように表示されることを確認する。
- passed 整形は true=pass、false=fail、null=n/a を固定する。特に range threshold を持つ length_compliance_rate が passed=n/a になることをテストで明示する。
- manifest.record_count と unique scope 数が一致しない synthetic case を作り、note 行が表示されることを確認する。ここでは mismatch を failure にしないことも固定する。
- manifest.json または run-metrics.json が欠ける場合の error path を追加し、CLI が 1 を返して不足ファイル名を含む error を出すことを確認する。
- tests/cli/test_live_smoke.py では run 実行後に report も叩き、run_id、suite_id、少なくとも 1 つの既知 metric 名、n=1 が出ることを確認する。live 値そのものは provider 実行結果に依存するため固定しすぎない。

## docs に固定すべきこと

- README.md に suites -> run -> report の最小導線を追加し、run directory から report を読む運用を 1 コマンドで示す。
- README.md では records が manifest.record_count、n が sample_count であり、同じ意味ではないことを短く説明する。
- docs/architecture/benchmark-foundation.md には、report CLI が single-run の stable 読み出し入口であること、既定表示の最小列、threshold / passed の整形方針、record_count と sample_count の意味差を追記する。
- docs では run-metrics.json の scope が model_key x prompt_id x prompt_category であること、比較レポート本体はこの row 正規化を再利用する前提であることを明記する。

# 次アクション

- programmer が report CLI の parser / renderer、README と architecture docs の最小追記、tests/cli の追加を実装する。
- reviewer が command 名、scope の見せ方、record_count と sample_count の意味差、range threshold の passed=n/a が docs / tests / 実装で一致しているかを確認する。

# 関連パス

- README.md
- docs/architecture/benchmark-foundation.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/benchmark/evaluation.py
- src/local_llm_benchmark/benchmark/runner.py
- src/local_llm_benchmark/storage/jsonl.py
- tests/cli/test_main.py
- tests/cli/test_live_smoke.py
- progress/reviewer/00009-05-review-roadmap-3-minimum-slice.md

# 設計対象

- run directory を受けて run-metrics を user-facing に読む single-run CLI 入口。
- scope、metric、sample_count、threshold、passed をどう最小表示に落とすか。
- 比較レポート本体の前段として、どこまでを今回固定し、どこから先を後段へ送るか。

# 設計判断

- command 名は report を採用し、artifact 名の metrics ではなく利用目的を表す。
- row の最小表示は scope.model_key、scope.prompt_category、scope.prompt_id、metric_name、value、threshold、passed、sample_count とする。
- record_count は header、sample_count は row で見せ、両者の意味差は legend / note で明示する。
- threshold が run gate として未評価な場合は passed を n/a とし、失敗表示へ誤読させない。
- 比較レポート本体は今回の artifact loader と row 正規化を再利用する前提とし、複数 run 集計や filter は後段へ送る。

# 影響範囲

- src/local_llm_benchmark/cli/main.py の subcommand 追加。
- cli 配下の report renderer / loader helper の追加。
- README.md と docs/architecture/benchmark-foundation.md の利用導線と用語説明の更新。
- tests/cli/test_main.py と tests/cli/test_live_smoke.py の report 経路 test 追加。
- storage schema と provider 実装には変更を要求しない。

# リスク

- run-metrics.threshold の range 形は run gate ではなく case 条件の表示に近いため、passed=n/a を知らないと誤読されやすい。
- 現状の scope は model_key x prompt_id で、sample_count が 1 になりやすい。ここを固定値だと誤解すると将来 multi-case 化で崩れる。
- report helper を CLI 直下へ置く最小実装は妥当だが、比較レポートが広がると shared loader 抽出が必要になる。

# 改善提案

- 比較レポート本体に進む段階で、manifest / run-metrics 読み出しと row 正規化だけを shared helper として切り出すと、single-run report と multi-run compare の責務を分けやすい。
- 後続で multi-case prompt を入れる場合も report の最小列は維持し、sample_count だけが自然に増える設計を守ると user-facing surface を壊しにくい。
- 追加の filter や JSON 出力は比較レポート本体で必要性が出てから入れ、今回の single-run 入口には持ち込まない。