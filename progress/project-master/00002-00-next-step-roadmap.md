---
request_id: "00002"
task_id: "00002-00"
parent_task_id:
owner: "project-master"
title: "next-step-roadmap"
status: "done"
depends_on: []
child_task_ids:
  - "00002-01"
created_at: "2026-04-17T21:10:00+09:00"
updated_at: "2026-04-17T21:45:00+09:00"
related_paths:
  - "README.md"
  - "docs/ollama"
  - "progress/solution-architect"
---

# 入力要件

- ユーザーが追加した Homebrew ベースの Ollama 導入手順を踏まえ、疎通確認結果が妥当か判断する。
- 次ステップへ進むためのロードマップを作る。
- ロードマップはプロジェクトルートの README 末尾へ追加する。

# 整理した要件

- 疎通確認は curl の version、tags、chat と CLI の ping、sample-run が通っていれば、現段階の基盤確認として十分とみなせる。
- ロードマップは、直近の成果物と整合し、README に短く実用的に載る粒度にする。
- project-master は progress と委譲を担当し、README 本文更新は専門役割へ委譲する。

# 作業内容

- README と docs/ollama の現状を確認し、ユーザー提示の疎通結果が現行の確認手順と整合することを確認した。
- 設計アーキテクト向けの子タスクを作成し、README 末尾へ追加するロードマップ作成を委譲する。
- 設計アーキテクトの結果を確認し、README 末尾へ現在地と 5 段階のロードマップが追記されたことを確認した。

# 判断

- 現在地としては、Ollama の導入、API 疎通、最小 benchmark 経路の確認まで完了しているため、次の優先順位は config 外部化、結果保存、評価データ整備、provider 拡張の順が妥当と判断する。
- README は短く保つルールがあるため、詳細設計ではなく段階と完了条件を示す形が適切と判断する。

# 成果

- request_id 00002 の親記録を作成した。
- README 末尾に、config 外部化、結果保存、評価データ整備、provider 拡張、比較レポート整備の順で次ステップのロードマップを追加した。
- 疎通確認結果について、curl と CLI の両経路が通っており、現段階の基盤確認として問題ないと判断できる状態を確認した。

# 次アクション

- 次に着手する実装タスクは config 外部化が最優先で、その後に ResultSink の永続化、評価データ整備へ進む。
- provider 拡張と比較レポート整備は、その前段の設定と保存形式が固まってから進める。

# 関連パス

- README.md
- docs/ollama
- progress/solution-architect