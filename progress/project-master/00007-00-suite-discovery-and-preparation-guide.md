---
request_id: "00007"
task_id: "00007-00"
parent_task_id:
owner: "project-master"
title: "suite-discovery-and-preparation-guide"
status: "done"
depends_on: []
child_task_ids:
  - "00007-01"
  - "00007-02"
  - "00007-03"
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-18T12:40:00+09:00"
related_paths:
  - "README.md"
  - "configs"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/suite_catalog.py"
  - "src/local_llm_benchmark/config"
  - "tests"
---

# 入力要件

- 利用可能な benchmark suite と、その suite で必要な provider / model が分かる導線が欲しい。
- 仲間へ config を共有するときに、何ができるか、何を準備すればよいかを確認しやすくしたい。
- 情報は user-friendly にするが、情報過多にはしない。
- 既に十分な仕組みがあるなら、状況報告のみで完了してよい。

# 整理した要件

- まず既存 CLI と README でこの要件を満たせるか確認する。
- 足りない場合は、suite 一覧と suite ごとの準備情報を短く表示する provider 非依存の仕組みを追加する。
- 表示内容は、次アクションへつながる最小構成に絞る。

# 作業内容

- progress ルール、Python 実装ルール、README、既存 CLI を確認し、現状は `run` のみで、suite 一覧や準備すべき model / provider を確認する導線が不足していることを把握した。
- 設計、実装、レビューの 3 子タスクへ分けて進める。
- 設計アーキテクトが、`suites` 1 コマンドで一覧と詳細の 2 段階表示にする案を採用し、一覧は選択用、詳細は準備確認用に責務を分ける方針を整理した。
- programmer が `local-llm-benchmark suites --config-root ...` と `local-llm-benchmark suites <suite_id> --config-root ...` を実装し、既存 config 解決結果から provider / model / prompt 情報を表示できるようにした。
- reviewer が README と help の導線ノイズを最小修正し、重大 finding なし、関連 tests 成功を確認した。

# 判断

- 現状の README には sample suite の説明はあるが、config を共有された側が「今ある suite 一覧」と「suite ごとに準備する model / provider」を CLI で確認する仕組みはない。
- したがって、状況報告のみでは足りず、suite discovery 用の導線を追加するのが妥当である。
- 一覧で必要なのは選択判断に必要な最小情報だけであり、generation 設定や selector の生値は出さない方が user-friendly である。
- provider 非依存を守るため、CLI は provider 固有の pull コマンドを出さず、provider_id と model identifier までに留めるのが妥当である。

# 成果

- request_id 00007 の親記録を作成した。
- 子タスク 00007-01, 00007-02, 00007-03 を用意した。
- 共通 CLI に `suites` サブコマンドを追加した。
- 一覧表示では、利用可能な suite 数、suite_id、概要、解決後の model 数 / prompt 数 / provider 要約を出せるようにした。
- 詳細表示では、概要、tags、prompt set、category、provider ごとの required model identifier、次の操作を出せるようにした。
- suite 情報の解決は新規モジュール `src/local_llm_benchmark/cli/suite_catalog.py` に閉じ込め、既存の config loader、model registry、prompt repository を再利用する形にした。
- README の最小実行に suite discovery 導線を追加し、install -> suites -> run の順でそのまま試せるようにした。
- レビュー時点で重大 finding はなく、関連 tests 6 件成功、diagnostic 0 件である。

# 次アクション

- README 記載そのままの `suites` -> `run` を確認する success-path smoke を、provider 利用可能環境で追加する。
- suite 数や provider 組み合わせが増えたら、必要に応じて `suites` の機械向け JSON 出力を検討する。

# 関連パス

- README.md
- configs
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/config
- tests