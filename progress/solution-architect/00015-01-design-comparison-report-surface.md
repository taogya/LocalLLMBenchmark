---
request_id: "00015"
task_id: "00015-01"
parent_task_id: "00015-00"
owner: "solution-architect"
title: "design-comparison-report-surface"
status: "done"
depends_on: []
created_at: "2026-04-18T23:20:00+09:00"
updated_at: "2026-04-18T23:58:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/report.py"
  - "src/local_llm_benchmark/storage/jsonl.py"
  - "tests/cli/test_main.py"
  - "docs/architecture/benchmark-foundation.md"
  - "progress/project-master/00011-00-run-metrics-usage-surface.md"
  - "progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md"
  - "progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md"
  - "progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md"
---

# 入力要件

- 保存済み結果からモデル別差分を見られる比較レポート整備を、最小スライスで設計したい。
- strict metric を semantic quality と誤読しにくい表示にしたい。
- コード実装はまだ行わず、programmer がすぐ着手できる実装境界、CLI 仕様、必要テストまで固めたい。

# 整理した要件

- 既存 single-run report helper をどう再利用して multi-run 比較へつなぐか。
- CLI 形状、入力、出力粒度、差分の並べ方を最小限でどう固定するか。
- strict gate であることを表示面でどう明示するか。
- OpenAI-compatible 比較や strict / tolerant split を後から載せても、最小比較 surface を壊さない責務境界にするか。

# 作業内容

- README.md、docs/architecture/benchmark-foundation.md、src/local_llm_benchmark/cli/report.py、src/local_llm_benchmark/cli/main.py、tests/cli/test_main.py、src/local_llm_benchmark/storage/jsonl.py を確認し、single-run report が manifest.json と run-metrics.json の stable loader と row renderer を既に持っていることを確認した。
- progress/project-master/00011-00-run-metrics-usage-surface.md と progress/solution-architect/00011-01-design-run-metrics-report-surface.md を確認し、request 00011 の設計意図が single-run の stable 入口を先に固定し、multi-run 比較はその row 正規化を再利用する前提であることを引き継いだ。
- progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md、progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md、progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md を確認し、比較 surface 側では strict machine-readable JSON gate と lexical / structural constraint-following を比較していることを legend と note で明示し、semantic quality の代理指標と読ませない必要があると整理した。
- manifest の plan_snapshot に provider_id と trace_metadata を後から参照できることを確認し、OpenAI-compatible の provenance 追加は storage schema を変えずに拡張できる前提を確認した。

# 判断

## 1. 既存 single-run report helper の再利用方針

- 比較 surface は src/local_llm_benchmark/cli/report.py の load_run_report(run_dir) を唯一の artifact loader として再利用する。compare 専用コードが manifest.json と run-metrics.json を直接読み直す設計は採らない。
- 既存の ReportMetricRow、SingleRunReport、threshold / passed formatter はそのまま共有し、multi-run 側は SingleRunReport.metric_rows を row key で引き直す薄い正規化だけを追加する。
- 単一責務は、artifact 読み出しと検証は load_run_report、single-run 出力は render_run_report、multi-run 出力は新しい render_comparison_report に分ける。新しい reporting 層や storage schema 変更までは持ち込まない。
- 既存 helper にある run_id 一致検証、数値 / threshold 整形、note 用の record_count 解釈は compare 側でも流用し、表示だけを増やす。

## 2. CLI 形状と入力

- 最小 CLI は report の拡張ではなく、新しい compare サブコマンドを採用する。single-run の report --run-dir は request 00011 で固定した stable surface であり、引数の個数で single-run と multi-run を切り替えると help、tests、運用説明が曖昧になるためである。
- 推奨形は local-llm-benchmark compare --run-dir <run_a> --run-dir <run_b> [--run-dir <run_c> ...] とする。--run-dir は repeatable option とし、入力順を保持し、先頭を baseline run として delta の基準に使う。
- 入力は明示的な run_dir 複数指定だけを最小実装スライスに含める。ディレクトリ配下の自動探索は、baseline の決め方が曖昧で、古い artifact を誤って混ぜやすく、テストも不安定になるため後段へ送る。
- compare は最低 2 つの run_dir を必須とし、duplicate path は error にする。run_id が重複する場合も label が曖昧になるため最小スライスでは error とし、必要なら将来 --label を追加する。
- suite_id は hard error にしない。将来の OpenAI-compatible 用 suite や provider 差し替え suite を阻害しないため、row は model_key | prompt_category | prompt_id | metric_name で揃え、suite_id が複数ある場合は header note で明示する。

## 3. 出力 surface の最小形

- 比較単位は model_key x prompt_category x prompt_id x metric_name の row に固定する。model 単位集計や prompt_category 集計は second aggregation になるため、最小スライスでは入れない。
- 各 run の metric_rows を union し、値が完全に同じ row は既定で省略する。差分 surface の目的は違いを見ることなので、default は differing rows のみを出し、identical rows は header の件数だけにする。
- row を出す条件は、value、passed、sample_count、threshold 表示、または row presence のいずれかが run 間で異なる場合とする。row が存在しない場合は missing と表示し、run error、auto 評価対象外、suite / plan 差分のいずれでも起こりうると note で説明する。
- 先頭 run を baseline にし、他 run には delta=value-baseline.value を表示する。pairwise 全比較は行数が増えすぎるため採らない。
- threshold は present な row で同一なら 1 回だけ表示し、異なる場合は threshold=varies と表示する。異なる threshold を error にせず可視化へ留めることで、将来の strict / tolerant split や閾値較正差分を阻害しない。
- sort は model_key、prompt_id、metric_name、baseline 以外の run 順とする。single-run report の並び方と近づけ、差分だけが増えた形にする。

## 4. strict gate を semantic quality と誤読させない legend / note

- compare 出力の header に固定 legend を置く。最小文言は、base=先頭の --run-dir、delta=value-base.value、n=sample_count、pass / fail は current strict gate の結果、である。
- さらに固定 note を置く。要点は、current compare が strict machine-readable JSON と explicit lexical / structural constraint-following の差分を表示しており、semantic quality、自然な rewrite 品質、wrapper 除去後の payload correctness は表していない、である。
- JSON 系の fail を semantic miss と誤読させないため、json_valid_rate / format_valid_rate は raw JSON-only contract を見る strict gate、constraint_pass_rate は exact lexical / structural contract を見る strict gate、と README と同じ粒度で説明する。
- passed=n/a は fail ではなく threshold 未評価を意味するため、single-run と同じ語彙を維持する。compare 側でも n/a を failure 列へ寄せない。

## 5. OpenAI-compatible と strict / tolerant split へ載せやすい拡張余地

- row key に provider 固有列を埋め込まない。比較軸はあくまで model_key | prompt_category | prompt_id | metric_name にし、OpenAI-compatible provenance が必要になったら run header 側へ provider_id や config_root 由来の label を足す。
- manifest.plan_snapshot.model_selector.provider_id と trace_metadata は既に保存されているため、後から compare header に run descriptor を追加しても storage schema 変更は不要である。
- strict / tolerant split は既存 metric を上書きせず、metric_name を分けて row を追加する前提にする。compare surface は metric_name を opaque に扱えば、新しい tolerant metric が増えても strict row と並列表示できる。
- 実装は loader / normalizer と text renderer を分ける。これにより、後から JSON 出力、all rows 表示、metric family ごとの grouping、OpenAI-compatible 用 label 追加を同じ loader の上に積める。

# 成果

- 最小比較 surface は、新しい compare サブコマンドと repeatable な --run-dir を採用する設計で固めた。
- 既存 single-run report helper は artifact loader と formatting helper として再利用し、比較側は row の union と baseline delta だけを追加する設計にした。
- 出力は model_key | prompt_category | prompt_id | metric_name の row 差分だけを既定表示し、identical rows は件数サマリへ逃がす方針にした。
- strict gate の legend / note は request 00014 の判断に合わせ、semantic quality の代理指標ではないことを compare header で固定表示する方針にした。
- OpenAI-compatible provenance と strict / tolerant split は、run header の追加情報と metric_name 拡張で後から載せる方針にし、storage schema 変更を避ける設計にした。

# 次アクション

- programmer は src/local_llm_benchmark/cli/main.py に compare サブコマンドを追加し、src/local_llm_benchmark/cli/report.py の loader / formatter を再利用して render_comparison_report を実装する。
- programmer は README.md と docs/architecture/benchmark-foundation.md に compare 導線、baseline と delta の意味、strict gate note を追記する。
- programmer は tests/cli/test_main.py に compare help、successful diff、identical row omission、missing row、suite_id mismatch note、duplicate run_id error を追加する。
- reviewer は strict gate note の文言、report と compare の責務境界、OpenAI-compatible と strict / tolerant split を阻害していないことを確認する。

# 関連パス

- README.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/cli/report.py
- src/local_llm_benchmark/storage/jsonl.py
- tests/cli/test_main.py
- docs/architecture/benchmark-foundation.md
- progress/project-master/00011-00-run-metrics-usage-surface.md
- progress/project-master/00014-00-assess-fail-validity-and-next-roadmap.md
- progress/evaluation-analyst/00014-01-assess-ollama-fail-validity.md
- progress/prompt-analyst/00014-02-review-json-and-required-phrase-contracts.md

# 設計対象

- 保存済み run artifact を複数読み、single-run report の row を基準に multi-run 差分を表示する CLI surface。
- strict metric を strict metric として読める legend / note。
- provider 拡張や metric 拡張を阻害しない比較単位と責務境界。

# 設計判断

- CLI は report 拡張ではなく compare サブコマンドを追加する。
- 入力は明示的な --run-dir 複数指定とし、先頭 run を baseline にする。
- 出力は row 単位の差分だけを既定表示し、model 集計や prompt 集計は後段へ送る。
- row key は model_key、prompt_category、prompt_id、metric_name とし、suite_id は note で補足する。
- strict gate の意味は header legend / note で固定し、semantic quality の代理指標と見せない。

# 影響範囲

- src/local_llm_benchmark/cli/main.py の compare parser / handler 追加。
- src/local_llm_benchmark/cli/report.py の compare renderer と row 正規化追加。
- README.md と docs/architecture/benchmark-foundation.md の compare 導線追加。
- tests/cli/test_main.py の synthetic compare test 追加。
- storage、evaluation、provider 実装の schema 変更は要求しない。

# リスク

- strict gate note が弱いと、json_valid_rate や constraint_pass_rate の差分を semantic quality 差と誤読されやすい。
- suite / plan が異なる run を compare すると missing row が増えるため、note がないと failure と見誤りやすい。
- report.py に責務を寄せすぎると compare 追加後に肥大化しうるため、programmer は loader と renderer の境界を崩さない方がよい。

# 改善提案

- 次段で必要になったら --all-rows、--label、--runs-root、JSON 出力を add-on option として足す。
- OpenAI-compatible 比較が常態化したら compare header に provider_id や config_root 由来の短い run descriptor を追加すると provenance が読みやすい。
- strict / tolerant split を入れる段階では metric_name を分け、compare 側では metric family ごとの grouping だけを追加し、strict row を上書きしない方がよい。