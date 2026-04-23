# TASK-00018-01 docs/design 未確定情報監査

- Status: done
- Role: solution-architect
- Parent: TASK-00018
- Related IDs: ROLE-00002, PROG-00103, FLW-00003, FLW-00007, CLI-00105, CLI-00109, CFG-00003, CFG-00601, CFG-00602, CFG-00603, PVD-00004, PVD-00406
- 起票日: 2026-04-23

## 目的

`docs/design/` を監査し、設計書に残すべき確定済み情報と、`progress/` や README ロードマップへ逃がすべき未確定情報を分類する。必要なら docs/design 側の記述修正案をまとめる。

## 完了条件

- 未確定情報の候補がファイル単位で列挙され、分類根拠がある。
- 将来拡張として残してよい「確定済み拡張境界」と、未確定ゆえ設計書から外すべき情報が区別されている。
- TASK-00012 に起因する `config lint` / `config dry-run` 記述について、設計書に残すべき範囲が明確になっている。
- 必要な docs/design 修正案または後続 task が示されている。

## スコープ外

- 実装コードの変更
- `.github/instructions/` の更新

## 監査結果

| 対象 | 判定 | 対応 |
| --- | --- | --- |
| docs/design/01-architecture.md の将来拡張節 | 確定済み拡張境界 | 節名と導入文を「確定済み拡張境界」に言い換え、例示は責務境界のみ残した |
| docs/design/04-workflows.md の `config lint` / `config dry-run` 記述 | 未確定情報の混入 | 将来コマンド名を除去し、FLW-00003 / FLW-00007 の入力境界と責務境界だけを残した |
| docs/design/05-cli-surface.md の将来コマンド名と「微調整可能」記述 | 未確定情報の混入 | `check` / `system-probe` の確定済み surface のみで責務を再記述し、CLI 名は現行 surface として固定した |
| docs/design/06-configuration-sources.md の「具体形式は実装で確定」系記述 | 未確定情報の混入 | 「本書の対象外」とする設計境界へ言い換え、将来コマンド名は一般化した |
| docs/design/07-provider-contract.md の `config dry-run` 記述 | 未確定情報の混入 | 非推論 probe 契約の再利用境界として一般化し、未確定な public surface 名を除去した |
| docs/design/02-components.md / docs/design/03-data-model.md の同種文言 | 監査中の追加検出 | 同じ基準で表現を整理し、docs/design 全体の運用ルールに揃えた |

## 残課題

- TASK-00013 側で config lint / dry-run の名称と public surface が確定した時点で、必要な新規 ID とともに docs/design へ反映する。
- reviewer は、将来 surface 名を除去した後も `check` / `system-probe` / Run 開始前検証の責務境界が十分に読めるかを確認する。

## 進捗ログ

- 2026-04-23 project-master: 起票。候補は project-master 側で抽出済みだが、最終的な分類と docs/design の扱いは solution-architect 判断に委ねる
- 2026-04-23 solution-architect: Status を `in-progress` として着手。`docs/design/01-architecture.md`, `docs/design/04-workflows.md`, `docs/design/05-cli-surface.md`, `docs/design/06-configuration-sources.md`, `docs/design/07-provider-contract.md` の候補記述を確認し、未確定な将来 public surface 名と、確定済みの責務境界を切り分ける方針を確定した。
- 2026-04-23 solution-architect: `docs/design/01-architecture.md`, `docs/design/02-components.md`, `docs/design/03-data-model.md`, `docs/design/04-workflows.md`, `docs/design/05-cli-surface.md`, `docs/design/06-configuration-sources.md`, `docs/design/07-provider-contract.md` を更新。将来コマンド名 (`config lint` / `config dry-run`) と「実装で後決めする」文言は docs/design から除去または一般化し、静的検証 / 動的観測 / 非推論 probe の確定済み境界だけを残した。完了条件を満たしたため Status を `review-pending` に更新した。
- 2026-04-23 solution-architect: reviewer task `TASK-00018-02` の合格と Status `done` を確認。差し戻し事項なしのため、本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- (未実施)
