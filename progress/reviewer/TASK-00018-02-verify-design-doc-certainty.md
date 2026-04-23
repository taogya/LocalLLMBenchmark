# TASK-00018-02 docs/design 未確定情報監査の確認

- Status: done
- Role: reviewer
- Parent: TASK-00018
- Related IDs: ROLE-00002, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00018-01 の監査結果を確認し、未確定情報の分類とルール追加が妥当かを判定する。

## 完了条件

- 未確定情報候補の分類に漏れや誤判定がない。
- 「設計書には確定した設計情報のみを書く」ルール追加が妥当である。
- TASK-00012 など進行中 task への影響が整理されている。

## スコープ外

- docs/design の新規設計執筆
- 実装コード変更

## 進捗ログ

- 2026-04-23 project-master: 起票。solution-architect による監査結果の確認用
- 2026-04-23 reviewer: [progress/solution-architect/TASK-00018-01-audit-design-doc-certainty.md](../solution-architect/TASK-00018-01-audit-design-doc-certainty.md)、[docs/design/01-architecture.md](../../docs/design/01-architecture.md)、[docs/design/02-components.md](../../docs/design/02-components.md)、[docs/design/03-data-model.md](../../docs/design/03-data-model.md)、[docs/design/04-workflows.md](../../docs/design/04-workflows.md)、[docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md)、[docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md)、[docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md)、[.github/instructions/documentation.instructions.md](../../.github/instructions/documentation.instructions.md) を確認。未確定名称 (`config lint` / `config dry-run`) と「実装で確定する」系表現が docs/design から除去または一般化され、`check` / `system-probe` / Run 開始前検証 / 非推論 probe の責務境界が十分読めることを確認した。TASK-00012 への不適切な影響はなく、`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK。差し戻し事項なしとして Status を `done` に更新した。

## レビュー記録 (reviewer 用)

### 判定

- 合格

### verify.sh 実行結果サマリ

- OK: check_id_format.py
- OK: check_id_uniqueness.py
- OK: check_id_references.py
- OK: check_doc_links.py
- OK: check_progress_format.py
- OK: check_mermaid_syntax.py
- OK: check_markdown_syntax.py
- OK: check_no_implementation_leak.py
- OK: check_role_boundary.py
- OK: check_oos_no_implementation.py

### 確認対象

- progress/solution-architect/TASK-00018-01-audit-design-doc-certainty.md
- docs/design/01-architecture.md
- docs/design/02-components.md
- docs/design/03-data-model.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- .github/instructions/documentation.instructions.md
- progress/project-master/TASK-00012-v1-2-0-system-probe.md (進行中 task 影響確認のみ)

### 発見事項

- 観点 1: 合格。solution-architect の分類は妥当で、将来 public surface 名 (`config lint` / `config dry-run`) と「実装で確定する」系の未確定表現は docs/design から除去または設計境界の一般論へ置換されている。[docs/design/01-architecture.md](../../docs/design/01-architecture.md) の拡張境界、[docs/design/04-workflows.md](../../docs/design/04-workflows.md)、[docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md)、[docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md)、[docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) の責務再記述は、監査結果 [progress/solution-architect/TASK-00018-01-audit-design-doc-certainty.md](../solution-architect/TASK-00018-01-audit-design-doc-certainty.md) と整合している。[docs/design/02-components.md](../../docs/design/02-components.md) と [docs/design/03-data-model.md](../../docs/design/03-data-model.md) にも同種の未確定名再混入は見当たらない。
- 観点 2: 合格。[.github/instructions/documentation.instructions.md](../../.github/instructions/documentation.instructions.md) に追加された「`docs/design/` には確定した設計情報のみを書く」ルールは、既存の「実装に踏み込まない」と矛盾せず、未確定事項を `progress/` や README ロードマップで管理する運用先も併記されているため妥当である。
- 観点 3: 合格。未確定名称を除去した後も責務境界は十分読める。[docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) の CLI-00105 / CLI-00109 と診断系責務境界、[docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md) の CFG-00601〜00603、[docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) の PVD-00406 により、`check` は静的整合性確認、`system-probe` は動的観測、Run 開始前検証や将来の事前確認面は抽象境界として保持する整理が崩れていない。
- 観点 4: 合格。TASK-00012 など進行中 task への不適切な影響はない。[progress/project-master/TASK-00012-v1-2-0-system-probe.md](../project-master/TASK-00012-v1-2-0-system-probe.md) でも、docs/design の未確定表現整理は blocker ではなく別 task で扱う論点として切り分け済みで、今回の docs/design 更新は既に確定した `check` / `system-probe` 境界を弱めていない。残る名称確定は TASK-00013 側に留まり、TASK-00012 の完了済み内容を巻き戻していない。

### 直接修正した範囲

- 本 reviewer task のレビュー記録更新のみ

### 差し戻し事項

- なし

### ユーザー報告可否

- 可。親 TASK-00018 はこの reviewer 結果をもって完了側へ進めてよい。