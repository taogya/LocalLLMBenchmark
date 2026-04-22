---
request_id: "00007"
task_id: "00007-02"
parent_task_id: "00007-00"
owner: "programmer"
title: "implement-suite-catalog-cli"
status: "done"
depends_on:
  - "00007-01"
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-18T11:45:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/suite_catalog.py"
  - "src/local_llm_benchmark/config"
  - "tests/cli/test_main.py"
  - "tests/cli/test_suite_catalog.py"
---

# 入力要件

- 利用可能な suite と準備すべき provider / model が分かる仕組みを実装したい。

# 整理した要件

- 設計に沿って provider 非依存の CLI と最小テストを追加する。
- 一覧は suite_id、概要、解決後の model 数 / prompt 数 / provider 要約に絞る。
- 詳細は概要、tags、prompt set と category 要約、provider ごとの required model identifier、最後の次アクションだけを出す。
- selector 解決は既存 loader、registry、prompt repository を再利用し、実行系と表示系のズレを避ける。

# 作業内容

- src/local_llm_benchmark/cli/main.py に suites サブコマンドを追加し、一覧と詳細の分岐を実装した。
- src/local_llm_benchmark/cli/suite_catalog.py を新設し、ConfigBundle から suite 一覧 / 詳細の表示 view と text renderer を実装した。
- 既存の InMemoryModelRegistry と InMemoryPromptRepository を使って resolved model / prompt を再計算し、provider 要約と required model identifier を生成するようにした。
- tests/cli/test_main.py に help、一覧、詳細、unknown suite の CLI テストを追加した。
- tests/cli/test_suite_catalog.py を追加し、suite 並び順と複数 provider の grouping を unit test で補強した。
- README.md に suite discovery の導線を短く追記した。

# 判断

- 表示ロジックは cli/main.py に埋め込まず、suite_catalog.py に閉じ込めて責務を分けた。
- description に含まれる task_id 接頭辞は CLI 表示時だけ除去し、内部管理用の文言をそのまま露出しないようにした。
- provider ごとの準備情報は provider 固有コマンドではなく model identifier 一覧だけを出し、共通 CLI を provider 非依存に保った。
- provider の並びは provider_id で安定化し、同一 provider 内の model identifier は解決順を保って情報量を抑えた。

# 成果

- local-llm-benchmark suites --config-root configs で suite 一覧を表示できるようになった。
- local-llm-benchmark suites <suite_id> --config-root configs で準備対象と次アクションを表示できるようになった。
- README から suite discovery の導線に入れるようになった。
- 関連 unit test を追加し、CLI の主要ケースを確認できる状態にした。

# 次アクション

- reviewer が information overload と provider 非依存性の観点で確認する。
- project-master が request 00007 の親 task へ結果を統合する。

# 関連パス

- README.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/cli/suite_catalog.py
- src/local_llm_benchmark/config
- tests/cli/test_main.py
- tests/cli/test_suite_catalog.py