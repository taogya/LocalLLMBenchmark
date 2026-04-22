# TASK-00006 実装着手前の残課題対応

- Status: done
- Role: project-master
- Related IDs: DAT-00109, SCR-00806, SCR-00807, ROLE-00004, NFR-00302

## 目的

ユーザー方針 (2026-04-19) に基づき、実装着手前に未対応の残課題を片付ける。CI 自動化は採用せず、reviewer ワークフローに組み込む方針へ変更。

## 完了条件

- DAT-00109 が「Comparison は最小 2 件以上の Run」に強化されている
- SCR-00806 / SCR-00807 の既定重みが「v1 smoke 後再評価」と本文で明示されている
- `.github/agents/reviewer.agent.md` の進め方に `MMDC_REQUIRED=1 bash scripts/verify.sh` 実行が組み込まれている
- `docs/development/release-criteria.md` に v1.0.0 smoke 観点チェックリストが追記されている

## 子 task

- TASK-00006-01 solution-architect: DAT-00109 強化 + SCR-00806/00807 注記 + release-criteria smoke チェックリスト追記
- TASK-00006-02 project-master: reviewer.agent.md に verify.sh 実行手順を組み込む (自分で実施)

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票
- 2026-04-19 project-master: TASK-00006-02 (reviewer.agent.md verify.sh 組み込み) 完了
- 2026-04-19 solution-architect: TASK-00006-01 完了 (DAT-00108/00109 強化、SCR-00806/00807 注記、release-criteria smoke チェックリスト追記)
- 2026-04-19 reviewer: TASK-00006-01 最終確認、verify.sh 全 OK、合格
- 2026-04-19 project-master: 親 task クローズ。実装フェーズ TASK-00007 へ移行
