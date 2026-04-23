# TASK-00014-05 provider status / model pull / model warmup 設計確定レビュー

- Status: done
- Role: reviewer
- Parent: TASK-00014
- Related IDs: REQ-00001, FUN-00408, FUN-00409, FUN-00410, CLI-00112, CLI-00113, CLI-00114, CLI-00309, PVD-00402, PVD-00406, PVD-00407, PVD-00408, PROG-00103
- 起票日: 2026-04-24

## 目的

TASK-00014-01 の設計変更を確認し、`provider status` / `model pull` / `model warmup` の仕様が実装着手条件を満たすかを判定する。あわせて、既存 `system-probe` / `config dry-run` と新 public surface の責務境界、旧 PVD 前提との整合に矛盾がないかを確認する。

## 完了条件

- TASK-00014-01 の成果が実装に十分な粒度で確定している。
- `provider status` / `system-probe`、`model warmup` / `config dry-run`、`model pull` / Provider Adapter の責務境界が矛盾なく整理されている。
- docs/design の TASK-00014 起因の追記に、旧前提との矛盾や未確定の名称 / 責務が既定仕様として混入していない。
- 差し戻し事項があれば、対象ファイルと論点を明記している。

## スコープ外

- `provider status` / `model pull` / `model warmup` 実装そのもの
- README 更新
- 最終レビュー

## 進捗ログ

- 2026-04-24 project-master: 起票。programmer 着手前に reviewer の設計確認を挟むため追加。
- 2026-04-24 project-master: 現行 docs/design では PVD-00402 / PVD-00406 が model pull / warm-up を責務外としているため、この整理が TASK-00014-01 で適切に更新または supersede されているかを重点確認事項として共有。
- 2026-04-24 reviewer: TASK-00014-01 と docs/requirements, docs/design, docs/development を確認。`provider status` / `system-probe`、`model warmup` / `config dry-run`、`model pull` の explicit acquisition と暗黙 pull 禁止、PVD / OOS supersede 連結、implementation leak 不在はいずれも docs 上で整合していると判断した。
- 2026-04-24 reviewer: `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行。9/10 OK だが `check_oos_no_implementation.py` が FAIL で、`progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md` の `Related IDs` に active task では許容されない OOS-00005 / OOS-00012 が残っていることを確認した。role boundary により他ロール task は修正せず、差し戻し事項として記録し、本 task を `review-pending` に更新した。
- 2026-04-24 reviewer: 差し戻し後の再確認として `progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md` を再読し、`Related IDs` から OOS-00005 / OOS-00012 が除去済みであることを確認した。対象 2 ファイルに `get_errors` で問題がないことを確認したうえで `MMDC_REQUIRED=1 bash scripts/verify.sh` を再実行し、10/10 OK を確認したため、本 task を `done` に更新した。programmer は TASK-00014-02 に着手可と判断する。

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

- progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md
- docs/requirements/02-functional.md
- docs/requirements/04-out-of-scope.md
- docs/design/02-components.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- docs/development/environment.md
- docs/development/release-criteria.md

### 発見事項

- 観点 1: 合格。`provider status` は provider inventory の直接確認、`system-probe` は host facts と登録済み Model Candidate の横断観測として、[docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) で一貫している。`provider status` 側に host facts や candidate cross-check は持ち込まれていない。
- 観点 2: 合格。`config dry-run` は Run 設定起点の read-only preflight、`model warmup` は provider / model target 起点の explicit preparation として、[docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) で整合している。warmup は actual provider execution を 1 回行うが、TaskProfile / Run 設定由来の prompt 組立は持ち込まない。
- 観点 3: 合格。`model pull` の explicit acquisition と暗黙 pull 禁止は、[docs/requirements/02-functional.md](../../docs/requirements/02-functional.md), [docs/requirements/04-out-of-scope.md](../../docs/requirements/04-out-of-scope.md), [docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md), [docs/development/environment.md](../../docs/development/environment.md), [docs/development/release-criteria.md](../../docs/development/release-criteria.md) で一致している。`run` / `system-probe` / `config dry-run` / `model warmup` が暗黙 pull を起動しない方針も崩れていない。
- 観点 4: 合格。旧前提の supersede 連結は docs 上で追跡可能で、OOS-00005 → OOS-00012 は [docs/requirements/04-out-of-scope.md](../../docs/requirements/04-out-of-scope.md) と [docs/development/environment.md](../../docs/development/environment.md)、PVD-00402 → PVD-00407 と PVD-00406 → PVD-00408 は [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) に明示されている。solution-architect task の進捗ログにも対応関係が列挙されている。
- 観点 5: 合格。対象 docs/design には HTTP endpoint 名、関数シグネチャ、未確定 TODO の混入は見当たらず、`check_no_implementation_leak.py` も OK だった。CLI 入力境界、出力最小セクション、終了コード、workflow、provider contract まで確定しており、programmer が実装方針を決めるのに十分な粒度に達している。
- 観点 6: 合格。前回差し戻し事項だった `progress/solution-architect/TASK-00014-01-design-provider-cli-warmup.md` の `Related IDs` から OOS-00005 / OOS-00012 が除去されており、`check_oos_no_implementation.py` を含む verify 10/10 OK を確認した。progress 運用上の阻害要因は解消済み。

### 直接修正した範囲

- 本 reviewer task の Status、Related IDs、進捗ログ、レビュー記録を更新

### 差し戻し事項

- なし

### programmer 着手可否

- 可。設計の責務境界と supersede 連結は docs / progress で整合しており、verify 10/10 OK も確認できたため、TASK-00014-02 の実装着手条件を満たしている。

### ユーザー報告可否

- 可。前回差し戻し事項は解消され、reviewer 観点と機械チェックの両方で阻害要因は残っていない。