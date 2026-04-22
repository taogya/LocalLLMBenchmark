---
request_id: "00006"
task_id: "00006-00"
parent_task_id:
owner: "project-master"
title: "scorer-definition-and-result-sink"
status: "done"
depends_on: []
child_task_ids:
  - "00006-01"
  - "00006-02"
  - "00006-03"
  - "00006-04"
created_at: "2026-04-18T00:20:00+09:00"
updated_at: "2026-04-18T02:15:00+09:00"
related_paths:
  - "README.md"
  - "docs/architecture"
  - "src/local_llm_benchmark/storage"
  - "src/local_llm_benchmark/cli/main.py"
  - "prompts"
  - "configs"
---

# 入力要件

- README から、モデルをどのようにダウンロードする想定なのか分かるようにしたい。
- pip パッケージ側で自動ダウンロードするのか、ユーザーが事前に取得するのかを明記したい。
- その後、scorer 定義と閾値の整理、ロードマップ 2 の ResultSink 実装をまとめて進めたい。

# 整理した要件

- README には、現在の方針として「モデル取得は provider ごとの責務であり、本パッケージは自動ダウンロードしない」ことを明示する。
- scorer 定義と閾値は、初期評価指標のうち実装に落とし込むものを固定し、何を記録するかまで決める。
- ResultSink は raw response と正規化済み record に加えて、評価条件の追跡に必要な metric_definition、scorer_version、reference_type などを保存できる形にする。
- project-master は progress 管理と委譲を担当し、評価設計、保存設計、実装、レビューを各 agent へ委譲する。

# 作業内容

- README、評価メモ、storage 抽象、prompt 定義、ResultSink stub の現状を確認し、モデル取得方針が README で未説明であること、scorer 定義と閾値は未固定であること、保存は stub のままであることを確認した。
- 評価設計、保存設計、実装、レビューの子タスクを作成する方針を固めた。
- 評価アナリストが deterministic scorer と quality scorer を切り分け、初期固定の scorer、閾値、保存すべき評価条件を docs と progress に整理した。
- 設計アーキテクトが ResultSink v1 の保存境界、records.jsonl と raw/ の分離、evaluation.conditions を含む保存スキーマ、CLI と runner の注入点を docs と progress に整理した。
- programmer が README のモデル取得方針を明記し、sample prompt metadata を fixed scorer 前提に更新し、JSONL ベースの ResultSink と関連テストを実装した。
- reviewer が README、prompt metadata、保存実装、docs、tests を確認し、軽微な整合修正 2 件を解消したうえで重大 finding なしと判断した。

# 判断

- モデル取得方針は provider 非依存思想に関わるため、README で早めに明示する価値が高い。
- scorer 定義だけを先に決めても、保存形式が追随しないと後で差分追跡が難しくなるため、ResultSink 実装とまとめて進める方がよい。

# 成果

- request_id 00006 の親記録を作成した。
- README に、このパッケージはモデル自動ダウンロードを行わず、sample suite を含め provider 側で事前取得する前提であることを明記した。
- 初期固定の deterministic scorer と閾値を整理し、classification、extraction、rewrite、summarization、short_qa、constrained_generation のうち自動評価で扱う範囲を docs と metadata に反映した。
- `tmp/results/<run_id>/` を既定出力先とする JSONL ResultSink を実装し、manifest.json、records.jsonl、raw/ へ raw response と normalized records を分離して保存できる状態にした。
- request_snapshot に prompt_snapshot、reference_snapshot、evaluation.conditions を保存できるようにし、後続の case 評価と run 集計へつなげられる状態にした。
- review 時点で重大 finding はなく、関連 unit tests 12 件成功、diagnostic 0 件、実 CLI の error-path で保存ファイル生成まで確認した。

# 次アクション

- provider 利用可能な環境で、README の最小実行をそのまま使う成功系 E2E smoke を追加する。
- `case-evaluations.jsonl` と `run-metrics.json` の実装に進み、今回保存した evaluation.conditions と 1 対 1 に対応する評価結果を出力できるようにする。
- `summarization`、`short_qa`、`constrained_generation` の sample prompt と evaluation_reference を追加し、初期 fixed scorer の適用範囲を広げる。

# 関連パス

- README.md
- docs/architecture
- src/local_llm_benchmark/storage
- src/local_llm_benchmark/cli/main.py
- prompts
- configs