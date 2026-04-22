# TASK-00002 .github 整備

- Status: review-pending
- Role: project-master
- Related IDs: ROLE-00001..ROLE-00005, PROG-00101..PROG-00103, TRC-00001..TRC-00104

## 目的

カスタムエージェント運用とドキュメントガバナンスを `.github/` に固定し、以降の依頼を project-master 経由で安定して回せるようにする。

## 完了条件

- `.github/copilot-instructions.md` に常時適用の最小方針が置かれている
- `.github/agents/` に 5 ロール分の `*.agent.md` が揃っている
- `.github/instructions/` に customization-governance / progress-tracking / documentation / traceability の 4 件が揃っている
- 既存設計ドキュメント (`docs/development/`) との重複を抑え、参照で繋いでいる

## スコープ外

- pull request / issue テンプレート (v1 スコープ外)
- CI workflow

## 進捗ログ

- 2026-04-19 project-master: 親 task 起票。docs/development の規約と重複しない方針で作成
- 2026-04-19 project-master: `.github/copilot-instructions.md` / 4 件の instructions / 5 件の agents を作成。docs/ 側を正本としつつ参照で繋ぐ構成にした
