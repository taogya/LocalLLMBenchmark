# progress 運用メモ

このディレクトリは、依頼ごとの進行管理を残すための作業記録置き場です。

## フォルダ名

- ルート名は progress のままにします。
- ここは静的なタスク定義置き場ではなく、進行状態、判断、成果を更新し続ける場所だからです。
- task や tasks という名称よりも、用途に対して progress の方が意図に合います。

## 役割

- progress/project-master は、依頼全体の親記録です。
- progress/<agent> は、各エージェントの子タスク記録です。
- 1 つのユーザー要求に対して request_id を 1 つ発行し、その request_id の下に複数 task をぶら下げます。

## ディレクトリ構成

- progress/project-master
- progress/solution-architect
- progress/prompt-analyst
- progress/evaluation-analyst
- progress/programmer
- progress/reviewer

## 基本ルール

- 依頼を受けたら、まず progress/project-master/00001-00-master-plan.md のような親記録を作成または更新します。
- プロジェクトマスターが委譲する前に、委譲先の progress/<agent>/00001-01-<slug>.md のような子タスクを必要数作成または更新します。
- 各エージェントは、自分の progress ファイルのみ更新します。
- 完了したら、親記録へ結果を統合します。

## ID とファイル名の規則

- request_id は 5 桁の 0 埋め数字にします。
- task_id は request_id と 2 桁の連番を組み合わせます。
- 親記録の例: 00001-00-master-plan.md
- 子タスクの例: 00001-01-provider-research.md
- slug は小文字英数字とハイフンを使います。

## 機械可読性

- すべての progress ファイルは YAML frontmatter を持たせます。
- 最低限、request_id、task_id、parent_task_id、owner、title、status、created_at、updated_at、related_paths を入れます。
- 親記録は child_task_ids を持ち、子タスクは depends_on を持てます。
- この形式に揃えると、後から Python スクリプトで進捗一覧や依存関係を集計できます。

## テンプレート

- 新しい記録は progress/_templates/task-template.md を元にします。