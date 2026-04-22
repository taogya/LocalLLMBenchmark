---
request_id: "00004"
task_id: "00004-00"
parent_task_id:
owner: "project-master"
title: "provider-neutral-config-externalization"
status: "done"
depends_on: []
child_task_ids:
  - "00004-01"
  - "00004-02"
  - "00004-03"
created_at: "2026-04-17T22:25:00+09:00"
updated_at: "2026-04-18T00:10:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark"
  - "tests"
  - ".github/instructions/python-benchmark.instructions.md"
---

# 入力要件

- provider 非依存のはずのファイルに `Ollama` という文字が散見されるため、思想に沿うよう修正する。
- 必要なら再発防止のルールも追加する。
- README にあるロードマップのうち、まず 1 の config 外部化から進める。
- モデル選定は現時点では 3 段階のランクを想定し、各ランク 1 モデルずつで最初の通し先を作る。

# 整理した要件

- provider 依存の処理や文言は providers 配下や provider 固有設定へ寄せ、benchmark core、config 抽象、共通 CLI 境界には持ち込まない。
- ロードマップ 1 は、in-memory stub から外部設定ファイル駆動へ移し、3 ランクの比較対象を設定として表現できる状態まで進める。
- ランク名は現時点の比較目的に対して 3 分割として扱い、将来の細分化余地を残す。
- project-master は progress 管理と委譲を担当し、設計、実装、最終確認は各 agent へ委譲する。

# 作業内容

- 現状コードを確認し、`cli/main.py` と `config/loader.py` に provider 固有表現が残っていること、README のロードマップ 1 がまだ未完了であることを確認した。
- 設計、実装、最終確認の 3 子タスクを作成し、順に委譲する準備を整えた。
- 設計アーキテクトが、provider 非依存境界、config 配置、3 ランク各 1 モデルの表現、generic CLI 契約を整理し、docs と Python 実装ルールへ反映した。
- programmer が、共通 CLI の generic run 化、TOML ベースの config loader、providers/factory.py、configs と prompts の外部設定、関連テスト、README と docs 更新を実装した。
- reviewer が、provider 非依存層の固有語混入がないこと、ロードマップ 1 が最小スコープで完了していること、9 tests 成功を確認し、軽微な loader エラー表示だけ最小修正した。

# 判断

- 単なる文字列置換ではなく、provider 非依存境界の定義と config 外部化の設計を先に固めた方が再修正が少ない。
- 3 ランク各 1 モデルという要件は、モデル registry と benchmark suite の設定構造へ先に織り込むべきで、コード内定数のままにしない方がよい。

# 成果

- request_id 00004 の親記録を作成した。
- provider 非依存層である cli/main.py と config/*.py から Ollama 固有コマンド、help 文言、既定 ID を除去した。
- `.github/instructions/python-benchmark.instructions.md` に、provider 非依存層へ provider 名を持ち込まないルールを追加した。
- TOML ベースの config 外部化を実装し、`configs/` と `prompts/` から 3 ランク各 1 モデルの baseline suite を読んで `local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1` で実行計画まで到達できる状態にした。
- README のロードマップ 1 を実装済みとして反映し、関連 docs を現行 CLI と設定構成に合わせて更新した。
- review 時点で重大 finding はなく、関連 unit tests 9 件成功と診断 0 件を確認した。

# 次アクション

- 次段階は README のロードマップ 2 である ResultSink の永続化に進む。
- 実 Ollama サーバーと対象 3 モデルがそろった環境で、generic CLI の成功系 E2E を別途確認する。
- provider profile を将来的に複数接続先へ拡張する場合は、provider_id 直結から profile_id への拡張を検討する。

# 関連パス

- README.md
- src/local_llm_benchmark
- tests
- .github/instructions/python-benchmark.instructions.md