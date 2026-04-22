---
request_id: "00007"
task_id: "00007-03"
parent_task_id: "00007-00"
owner: "reviewer"
title: "review-suite-catalog-cli"
status: "done"
depends_on:
  - "00007-02"
created_at: "2026-04-17T23:20:00+09:00"
updated_at: "2026-04-18T12:35:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/cli/suite_catalog.py"
  - "tests/cli/test_main.py"
  - "tests/cli/test_suite_catalog.py"
  - "configs/benchmark_suites/local-three-tier-baseline-v1.toml"
  - "configs/model_registry/local-models-v1.toml"
---

# 入力要件

- suite discovery 用 CLI と文書が、分かりやすく、過不足なく、provider 非依存になっているか確認したい。

# 整理した要件

- 利用可能な suite と必要な provider / model が分かるかを、一覧と詳細の両方で確認する。
- provider 非依存の共通層に provider 固有コマンドや文言が漏れていないか確認する。
- エラー時の挙動と tests、README の導線が実用的か確認し、軽微な不整合は最小修正で閉じる。

# 作業内容

- src/local_llm_benchmark/cli/main.py、src/local_llm_benchmark/cli/suite_catalog.py、tests/cli/test_main.py、tests/cli/test_suite_catalog.py、README.md、sample config を確認し、一覧と詳細の責務分離、provider / model 表示、README 導線、エラー経路の扱いをレビューした。
- configs/benchmark_suites/local-three-tier-baseline-v1.toml と configs/model_registry/local-models-v1.toml を照合し、suite detail に出る provider と model identifier が sample config の実体と一致することを確認した。
- 軽微な整合修正として、README の suite discovery コマンドを install 後にそのまま試せる順序へ整理し、CLI help から内部 task_id を除去した。あわせて tests/cli/test_main.py に help 出力の回帰確認を追加した。
- get_errors で変更ファイルの診断を確認し、`source .venv/bin/activate && python -m unittest tests.cli.test_main tests.cli.test_suite_catalog` で関連 tests を再実行した。

# 判断

- suite 一覧は suite_id、概要、解決後 model 数 / prompt 数 / provider 要約に絞られており、情報量は抑えつつ選択に必要な情報を満たしている。
- suite 詳細は prompt set / category と provider ごとの required model identifier に絞られており、「何を準備するか」を README に戻らず確認できる。
- 共通 CLI と suite_catalog 表示には provider 固有コマンドが含まれておらず、sample config 由来の provider_id と model identifier だけが露出しているため、provider 非依存境界は保たれている。
- unknown suite の CLI error-path と help の provider 中立性は tests で押さえられており、suite discovery 追加分としては十分な最小カバレッジがある。
- README は suite discovery の導線自体は短いが、修正前は install より先に CLI 例が置かれており、そのまま貼って試せる形になっていなかったため、軽微事項としてレビュー内で修正した。

# 成果

 - 確認対象:
  - README.md
  - src/local_llm_benchmark/cli/main.py
  - src/local_llm_benchmark/cli/suite_catalog.py
  - tests/cli/test_main.py
  - tests/cli/test_suite_catalog.py
  - configs/benchmark_suites/local-three-tier-baseline-v1.toml
  - configs/model_registry/local-models-v1.toml
 - 発見事項:
  - 解消済み軽微事項: README の suite discovery コマンドが install 前に置かれており、そのまま貼って試せる導線になっていなかったため、README.md を最小修正して install -> suites -> run の順へ整理した。
  - 解消済み軽微事項: `local-llm-benchmark --help` に内部 task_id が表示されており、suite discovery の利用導線としては不要なノイズだったため、src/local_llm_benchmark/cli/main.py の description から除去し、tests/cli/test_main.py に回帰確認を追加した。
  - 未解消の重大 finding はなし。
 - 残課題:
  - 実 provider が利用可能な環境での success-path E2E は未確認であり、現在確認できているのは config 解決と unit test、error-path までである。
  - provider ごとに同一 model identifier を複数 model_key で共有する suite が将来入る場合、detail 表示は準備対象を優先して identifier を重複排除するため、実行上の model 件数との差をどう見せるかは後続検討余地がある。
 - ユーザー報告可否:
  - 可能。重大なブロッカーはなく、軽微な導線ノイズはレビュー内で解消済みである。
 - 改善提案:
  - 実 provider が使える環境で、`local-llm-benchmark suites ...` と `run ...` を README の記載そのままで確認する smoke を 1 本足すと、導線の実用性を継続確認しやすい。
  - suite が増えて provider / model 組み合わせが複雑になった段階で、必要なら `suites <suite_id> --format json` のような機械向け出力を追加すると共有時の再利用性が上がる。

# 次アクション

- project-master へ、重大 finding なし、軽微な導線修正 2 件をレビュー内で解消済み、関連 tests 成功という結果を引き継ぐ。

# 関連パス

- README.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/config
- tests