---
request_id: "00003"
task_id: "00003-00"
parent_task_id:
owner: "project-master"
title: "ignore-generated-python-artifacts"
status: "done"
depends_on: []
child_task_ids:
  - "00003-01"
created_at: "2026-04-17T21:55:00+09:00"
updated_at: "2026-04-17T22:15:00+09:00"
related_paths:
  - ".gitignore"
  - "src/local_llm_benchmark.egg-info"
---

# 入力要件

- `*.egg-info` は push 対象外でよいか判断する。
- そのほか push 対象外にしておくべき生成物があれば `.gitignore` に追記する。

# 整理した要件

- Python パッケージの生成物、仮想環境、テストや lint のキャッシュのうち、再生成可能でリポジトリに保持する意味が薄いものは ignore 対象とする。
- `.python-version` のような開発前提を共有する設定ファイルは、生成物ではないため ignore 対象に含めない。
- project-master は progress と委譲を担当し、`.gitignore` と生成物整理は programmer へ委譲する。

# 作業内容

- 現在の `.gitignore` とワークスペースを確認し、`.venv/` が未登録であること、`src/local_llm_benchmark.egg-info/` が存在することを確認した。
- programmer 向け子タスクを作成し、`.gitignore` 更新と既存生成物整理を委譲する。
- programmer の結果を確認し、`.gitignore` に Python 生成物とキャッシュの ignore が追加され、`src/local_llm_benchmark.egg-info/` が整理されたことを確認した。

# 判断

- `*.egg-info` は setuptools の生成物であり、ソースではないため push 対象外でよい。
- 今回は Python 開発で発生しやすい最小限の生成物を ignore し、環境共有に必要な `.python-version` は保持する方針が妥当と判断する。

# 成果

- request_id 00003 の親記録を作成した。
- `.gitignore` に `*.egg-info/`、`.venv/`、Python ビルド成果物、test/lint/coverage の代表的なキャッシュを追加した。
- `src/local_llm_benchmark.egg-info/` は生成物として作業ツリーから削除された。
- `*.egg-info` は push 対象外でよい、という判断を反映できる状態にした。

# 次アクション

- 今後もし既に追跡済みの生成物が見つかった場合は、`.gitignore` 追加とは別に git の index から外す対応を行う。

# 関連パス

- .gitignore
- src/local_llm_benchmark.egg-info