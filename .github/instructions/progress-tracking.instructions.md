---
description: "progress/**/*.md にタスク記録を作成または更新するときに使う。進行管理ファイルの正本、粒度、更新ルールを定義する。"
name: "progress 運用ルール"
applyTo: "progress/**/*.md"
---

# progress 運用ルール

- progress は静的なタスク一覧ではなく、進行状態と判断ログを残す場所として使う。
- 1 つのユーザー要求に対して 1 つの request_id を発行する。request_id は 5 桁の 0 埋め数字とする。
- task_id は request_id と 2 桁の連番を組み合わせた識別子とし、形式は 00001-00 のようにする。
- 親記録は progress/project-master/00001-00-master-plan.md のように置く。
- 子タスクは progress/<agent>/00001-01-<slug>.md のように置く。同じ agent に複数タスクがあってよい。
- slug は小文字英数字とハイフンで表す。
- すべての progress ファイルは YAML frontmatter を持ち、request_id、task_id、parent_task_id、owner、title、status、created_at、updated_at、related_paths を持つ。
- 子タスクは parent_task_id で親記録を参照する。依存関係がある場合は depends_on に task_id 配列で書く。
- 親記録は child_task_ids を持ち、子タスク一覧を追跡できるようにする。
- プロジェクトマスターは、委譲前に必要な数だけ子タスクを作成または更新する。
- 各 agent は、自分の担当 progress ファイルだけを更新し、他 agent の作業ログを書き換えない。
- 1 ファイル 1 タスクを原則とし、別タスクの内容を混在させない。
- status は todo、doing、blocked、done、cancelled のいずれかを使う。
- frontmatter に加えて、要件整理、作業内容、判断、成果、次アクションの本文を残す。
- 完了したら status を done にし、project-master 側へ結果を統合する。
- 長い思考ログは残さず、次の担当者が判断できる要点だけを書く。
- Python スクリプトなどで機械的に集計できるよう、frontmatter のキー名と形式は統一する。