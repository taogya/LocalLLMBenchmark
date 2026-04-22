---
request_id: "00001"
task_id: "00001-03"
parent_task_id: "00001-00"
owner: "programmer"
title: "bootstrap-docs-and-scaffold"
status: "done"
depends_on:
  - "00001-01"
  - "00001-02"
created_at: "2026-04-17T00:00:00+09:00"
updated_at: "2026-04-17T18:30:00+09:00"
related_paths:
  - "docs/ollama"
  - "pyproject.toml"
  - "src/local_llm_benchmark"
  - "tests"
---

# 入力要件

- docs/ollama 配下に開発環境構築と API 疎通確認までの手順を作る。
- provider 非依存の benchmark ベース実装を最小限で用意する。
- 入出力保存はスタブでよい。

# 整理した要件

- Ollama の一次情報を確認したうえで、導入、起動、モデル pull、疎通確認の文書を作る。
- 設計タスクの結果に沿って provider 非依存の最小スキャフォールドを作る。
- suite -> model -> prompt の解決責務は runner 側に維持する。
- 実装範囲の確認手段として CLI と unit test を用意する。

# 作業内容

- docs/ollama/README.md、docs/ollama/macos-setup.md、docs/ollama/api-check.md を追加し、macOS 前提、pyenv + venv、Ollama 導入、起動、モデル取得、curl 疎通確認、リポジトリ CLI 確認を日本語で整理した。
- pyproject.toml を追加し、src レイアウトの最小パッケージを editable install できるようにした。
- src/local_llm_benchmark 配下に benchmark core、config stub、model registry、prompt repository、providers/base、providers/ollama、storage stub、CLI を追加した。
- CLI として `local-llm-benchmark ollama ping` と `local-llm-benchmark sample-run` を実装した。
- tests 配下に runner、prompt repository、Ollama adapter、CLI の単体テストを追加した。

# 判断

- HTTP 実装は標準ライブラリ優先の方針に合わせ、urllib.request を採用した。
- config の外部ファイル読み込みは見送り、in-memory bootstrap stub で最小動作経路を固めた。
- 保存は NoOp と MemoryResultSink に留め、本実装の永続化仕様は後続へ分離した。
- prompt 変数展開は簡単なテンプレート置換までに留め、複雑な検証やデータセット連携は次段階へ送った。

# 検証

- `get_errors` で src/tests の診断を確認し、追加コードのスタイルエラーを修正した。
- これから `python -m unittest` と CLI の help 実行で最終確認する。

# 成果

- provider 非依存の benchmark runner と dataclass/Protocol の最小土台を実装した。
- Ollama client/adapter と CLI 疎通確認経路を実装した。
- セットアップ文書と API 確認手順を docs/ollama に追加した。

# 次アクション

- 外部設定ファイル loader を追加し、suite や registry をファイル駆動へ移す。
- ResultSink の永続化形式を決め、raw response と正規化 record の保存仕様を固める。
- provider 共通の受け入れテストを整え、将来 provider 追加時の再利用性を上げる。

# 関連パス

- docs/ollama
- pyproject.toml
- src/local_llm_benchmark
- tests
