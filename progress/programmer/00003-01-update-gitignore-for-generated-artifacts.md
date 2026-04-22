---
request_id: "00003"
task_id: "00003-01"
parent_task_id: "00003-00"
owner: "programmer"
title: "update-gitignore-for-generated-artifacts"
status: "done"
depends_on: []
created_at: "2026-04-17T21:55:00+09:00"
updated_at: "2026-04-17T22:10:00+09:00"
related_paths:
  - ".gitignore"
  - ".venv"
  - "src/local_llm_benchmark.egg-info"
---

# 入力要件

- `*.egg-info` を push 対象外にしたい。
- そのほか push 対象外にしておくべき生成物があれば `.gitignore` に追記する。

# 整理した要件

- `.gitignore` は最小だが実用的な Python 開発向け ignore に整える。
- 既存のソースや docs には触れない。
- `src/local_llm_benchmark.egg-info/` が生成物なら削除し、今後は `.gitignore` で再追跡を防ぐ。
- `.python-version` は共有前提のため ignore 対象へ含めない。

# 作業内容

- `.gitignore` に `*.egg-info/`、`.venv/`、`build/`、`dist/`、`pip-wheel-metadata/`、`*.py[cod]`、`.pytest_cache/`、`.ruff_cache/`、`.mypy_cache/`、`.coverage*`、`coverage.xml`、`htmlcov/` を追加し、Python パッケージ生成物と代表的な test/lint キャッシュを push 対象外にした。
- untracked だった `src/local_llm_benchmark.egg-info/` を削除し、作業ツリーから整理した。
- 差分と診断を再確認し、今回の変更が `.gitignore` と担当 progress に閉じていることを確認した。

# 判断

- `egg-info`、仮想環境、ビルド成果物、テストや lint のキャッシュは生成物として ignore 対象にするのが妥当。
- ignore 範囲は Python 開発で再生成されやすい成果物に限定し、`.python-version` や既存ソースは維持した。
- `.gitignore` を追加しても既に追跡済みのファイルは自動では管理対象外にならないため、将来そのような生成物が追跡済みなら `git rm --cached` が別途必要になる。

# 検証

- `git status --short .gitignore progress/programmer/00003-01-update-gitignore-for-generated-artifacts.md src/local_llm_benchmark.egg-info` で、`src/local_llm_benchmark.egg-info/` が untracked 生成物であることを確認してから整理した。
- 生成物候補を検索し、現時点で追加整理が必要なキャッシュ類は存在しないことを確認した。
- 更新後に `get_changed_files` と `get_errors` を実行し、差分が意図どおりであることと、今回編集したファイルに追加エラーがないことを確認した。
- 最後に `git status --short --ignored .gitignore .venv src/local_llm_benchmark.egg-info progress/programmer/00003-01-update-gitignore-for-generated-artifacts.md` を実行し、`.venv/` が ignore 済みで、`src/local_llm_benchmark.egg-info/` が作業ツリーから消えていることを確認した。

# 成果

- `.gitignore` を、このリポジトリに妥当な最小限の Python 生成物 ignore に更新した。
- `src/local_llm_benchmark.egg-info/` を作業ツリーから削除し、今後の再生成でも差分に出にくい状態にした。
- push 前に確認すべき注意点として、既存追跡済み生成物には `.gitignore` だけでは効かない前提を progress に残した。

# 次アクション

- project-master 側でこの結果を request_id 00003 の親記録へ統合する。

# 関連パス

- .gitignore
- .venv
- src/local_llm_benchmark.egg-info