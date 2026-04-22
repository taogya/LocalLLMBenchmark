# 進行管理ルール (Progress)

本プロジェクトは前プロジェクトと同様、ロール別ディレクトリで task を管理します。前プロジェクトの肥大と未稼働ロールの教訓を踏まえ、ファイル数と粒度を絞ります。

## ディレクトリ構成

```
progress/
  README.md                    # 本書からの抜粋。運用入口
  _templates/
    task-template.md           # task ファイル雛形
  project-master/              # ROLE-00001 が起票
  solution-architect/          # ROLE-00002 が起票
  programmer/                  # ROLE-00003 が起票
  reviewer/                    # ROLE-00004 が起票
  docs-writer/                 # ROLE-00005 が起票
```

## task ID 規約

- 形式: `TASK-NNNNN-SS`
  - NNNNN: 5 桁 0 埋めの親 task 連番
  - SS: 2 桁 0 埋めの子 task 連番 (子がない場合は省略)
- 起票時の親 task 採番は project-master の責務とする。子 task はロール側が連番を決める。
- ファイル名: `TASK-NNNNN-SS-<short-slug>.md`
- 親 task は project-master ディレクトリに配置する。

## task の状態

| 状態 | 意味 |
| --- | --- |
| open | 起票済み、未着手 |
| in-progress | 担当ロールが作業中 |
| review-pending | 完了報告済み、reviewer 待ち |
| done | reviewer の確認完了 |
| cancelled | 中止。理由を本文に残す |

状態は task 本文先頭の `Status:` フィールドで管理し、ファイル移動はしない。

## 起票・進行ルール

- ユーザーからの依頼は必ず project-master が親 task で受ける。
- 子 task はロールごとに独立して起票し、親 task からリンクする。
- 1 task 1 目的とし、複数の独立した目的を 1 task に詰めない。
- task 本文にはトレース対象 ID (REQ-, FUN-, ARCH- 等) を明記する。

## 完了基準

- 子 task: 担当ロールが本文の完了条件を満たし、`Status: review-pending` にする。
- 親 task: 配下の子 task がすべて `done`、もしくは `cancelled` になっていること。
- reviewer が `done` を付与する権限を持つ唯一のロールである (project-master の親 task 完了判定を除く)。

## 1 親 task に含めて良い子 task の上限

目安として 5 件以内。これを超える場合、親 task の分割を solution-architect に依頼する。

## 依頼テンプレート

雛形は `_templates/task-template.md` を参照する。最低限の項目は次のとおり。

- 親 task / 子 task 識別子
- 担当ロール
- 状態
- 関連要件 / 設計 ID
- 完了条件
- 進捗ログ (追記式)

## 既知の運用リスクと対策

| ID | リスク | 対策 |
| --- | --- | --- |
| PROG-00101 | task が肥大し読まれなくなる | 1 task 1 目的、親 task は配下リンクのみ |
| PROG-00102 | reviewer 不在で done 判定が緩む | reviewer 不在時は親 task を `review-pending` のまま保留 |
| PROG-00103 | 設計と実装の同時走行で齟齬発生 | 設計確定 (`done`) を実装着手の前提とする |
