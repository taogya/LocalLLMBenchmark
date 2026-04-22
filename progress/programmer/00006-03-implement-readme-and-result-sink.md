---
request_id: "00006"
task_id: "00006-03"
parent_task_id: "00006-00"
owner: "programmer"
title: "implement-readme-and-result-sink"
status: "done"
depends_on:
  - "00006-01"
  - "00006-02"
created_at: "2026-04-18T00:20:00+09:00"
updated_at: "2026-04-18T10:45:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/storage"
  - "src/local_llm_benchmark/cli/main.py"
  - "src/local_llm_benchmark/benchmark"
  - "prompts"
  - "tests"
  - "docs/architecture"
---

# 入力要件

- README にモデル取得方針を明記する。
- scorer 定義と閾値を反映する。
- ロードマップ 2 の ResultSink を実装する。

# 整理した要件

- 設計結果に沿って、README、docs、storage 実装、CLI、テストを更新する。
- モデル取得は provider ごとの責務であることを README に明記する。
- 保存形式は raw response と正規化 record、評価条件の追跡に必要な情報を残せるようにする。

# 作業内容

- README に、モデル取得は provider ごとの責務であり、このパッケージは自動ダウンロードしないこと、sample suite のモデルは事前取得が必要なこと、Ollama sample config の具体例を追記した。
- benchmark/evaluation.py を追加し、固定 scorer 定義から request_snapshot.prompt_snapshot と request_snapshot.evaluation.conditions を組み立てるようにした。
- storage/jsonl.py に JsonlResultSink を追加し、tmp/results/<run_id>/ 配下へ manifest.json、records.jsonl、raw/ を保存するようにした。records には raw_response を埋め込まず、raw_response_path を保存する形にした。
- CLI を JsonlResultSink 既定注入へ切り替え、`--output-dir` option を追加した。summary に result_dir も出すようにした。
- sample prompt 3 件の evaluation_metadata、output_contract、metadata.evaluation_reference を固定 scorer 定義に合わせて更新した。
- runner、storage、CLI の最小確認テストを更新・追加し、progress を完了状態へ更新した。

# 判断

- BenchmarkRecord dataclass は変更せず、request_snapshot の入れ子だけを広げる方針を採用した。既存のテストと呼び出し側への影響が最小だからである。
- scorer 条件の解決は sink ではなく runner 前段の helper に寄せた。保存実装を prompt 解釈から切り離し、JSONL sink を保存専任に保つためである。
- raw response は records.jsonl から分離し、run_id 配下の raw/ へ自己記述的な JSON として保存した。JSONL の肥大化を避けつつ、再確認に必要な provider payload を残せる。
- rewrite の quality scorer は無理に実装せず、machine-readable な constraint_pass 前提へ prompt を寄せるだけに留めた。

# 成果

- README だけで、モデル自動ダウンロードをしない方針と sample suite の事前取得前提が分かるようになった。
- sample prompt の evaluation metadata が manual_check から固定 scorer ベースへそろい、runner が metric 単位の evaluation.conditions を request snapshot へ保存できるようになった。
- CLI 実行で既定の `tmp/results/<run_id>/` に manifest.json、records.jsonl、raw/ が生成されるようになった。
- runner snapshot、storage 出力、CLI 実行の最小テストを追加または更新した。

# 検証

- `get_errors` で変更ファイルの診断を確認する。
- `PYTHONPATH=src .venv/bin/python -m unittest tests.benchmark.test_runner tests.storage.test_jsonl tests.cli.test_main` を実行して、runner snapshot、storage 出力、CLI 実行の最小確認を行う。

# 次アクション

- reviewer へ最終確認を依頼する。

# 関連パス

- README.md
- src/local_llm_benchmark/storage
- src/local_llm_benchmark/cli/main.py
- tests
- docs/architecture