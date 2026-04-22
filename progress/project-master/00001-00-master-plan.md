---
request_id: "00001"
task_id: "00001-00"
parent_task_id:
owner: "project-master"
title: "ollama-bootstrap-and-benchmark-foundation"
status: "done"
depends_on: []
child_task_ids:
  - "00001-01"
  - "00001-02"
  - "00001-03"
  - "00001-04"
  - "00001-05"
  - "00001-06"
  - "00001-07"
  - "00001-08"
created_at: "2026-04-17T00:00:00+09:00"
updated_at: "2026-04-17T20:55:00+09:00"
related_paths:
  - "README.md"
  - "docs/ollama"
  - "src"
  - "tests"
---

# 入力要件

- Ollama を利用したベンチマークツール作成に向け、開発環境構築と API 疎通確認までの手順を docs/ollama 配下に整備する。
- Ollama 固定ではなく、将来ほかのローカル推論手段にも展開できる評価ツールのベースを整備する。
- この時点では入出力ファイルの詳細設計は不要で、必要ならスタブでよい。
- config 管理、model 管理、評価データ用の prompt 管理の設計方針を定義する。

# 整理した要件

- 有効要件:
  - Ollama の導入、起動、モデル取得、API 疎通確認の実務手順を初心者でも追える形で文書化する。
  - provider 非依存の benchmark コア、provider adapter、config、prompt corpus の責務境界を先に定義する。
  - 最小限の Python スキャフォールドを作り、今後の provider 追加先を明確にする。
- 任意要件:
  - 実行結果保存は今回はスタブでよい。
  - 評価指標の詳細定義は次段階に回せる。
- 注意点:
  - Ollama の手順は変化しうるため、公式情報に沿うこと。
  - 既存ワークツリーには .github 配下の未コミット変更があるため、今回の作業では触れない。

# 作業内容

- 設計アーキテクトへ全体アーキテクチャと責務分割を委譲する。
- プロンプトアナリストへ prompt corpus と config レコード設計を委譲する。
- プログラマーへ docs/ollama の文書化と初期スキャフォールド実装を委譲する。
- プログラマーへスタイル診断の解消とテスト実行を追加で委譲する。
- プログラマーへ検証で生成された生成物のクリーンアップを委譲する。
- プログラマーへ残っている cli/main.py の型診断解消を委譲する。
- レビュアーへ最終整合性確認を依頼する。

# 判断

- docs と実装は並行可能だが、ベース実装は設計判断を先に受けてから着手する。
- prompt 管理は provider 実装から切り離し、設定データとして扱う方針を優先する。

# 成果

- 設計、prompt/config 設計、docs/ollama、最小スキャフォールドの初版がそろった。
- スタイル診断解消、最小検証、生成物整理、型診断解消、最終レビューまで完了した。
- docs、設計メモ、Python スキャフォールド、単体テストの整合を確認し、レビュー時点で 6 tests 成功と診断 0 件を確定した。

# 次アクション

- 次段階では config loader の外部ファイル化、result sink の永続化、実 Ollama API での疎通再確認を行う。

# 関連パス

- README.md
- docs/ollama
- src
- tests
