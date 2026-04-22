---
description: "progress/**/*.md にタスクを起票・更新するときに使う。task ID 形式と最小フォーマットを定義する。"
name: "progress 運用ルール"
applyTo: "progress/**/*.md"
---

# progress 運用ルール

正本は [docs/development/progress.md](../../docs/development/progress.md) です。本書は task ファイルを書くときの実務ルールに絞ります。

## task ID

- 形式: `TASK-NNNNN-SS`
  - `NNNNN`: 5 桁 0 埋めの親 task 連番
  - `SS`: 2 桁 0 埋めの子 task 連番。子がない場合は省略
- 親 task は `progress/project-master/` に配置する。子 task は対応するロールのディレクトリに配置する。
- ファイル名: `TASK-NNNNN-SS-<short-slug>.md`。slug は小文字英数字とハイフンのみ。

## 最小フォーマット

`progress/_templates/task-template.md` を雛形とする。task 本文は次の項目を必ず含める。

- 状態 (`Status:` フィールド)
- 担当ロール (`Role:`)
- 親 task 参照 (子 task のみ `Parent:`)
- 関連 ID (`Related IDs:` に REQ-, FUN-, NFR-, ARCH-, COMP-, DAT-, FLW-, OOS-, ROLE-, TRC- などを列挙)
- 目的 / 完了条件 / スコープ外 / 進捗ログ

## 状態遷移

- `open` → `in-progress` → `review-pending` → `done`
- 中止時は `cancelled`。理由を本文に残す
- ファイル移動はしない。状態変更のみで管理する

## 担当範囲

- 各ロールは自分のディレクトリ配下の task のみ更新する。他ロールの task 本文を書き換えない。
- 1 ファイル 1 task。複数の独立目的を 1 task に詰めない。

## 連結

- 子 task は本文先頭の `Parent:` で親 task を参照する。
- 親 task は配下の子 task を進捗ログ等から辿れるようにする (リンク or task ID 列挙)。

## 完了

- 子 task: 担当ロールが完了条件を満たしたら `Status: review-pending` にする。
- 親 task: 配下の子 task がすべて `done` または `cancelled` になった上で reviewer が `done` を付ける。
