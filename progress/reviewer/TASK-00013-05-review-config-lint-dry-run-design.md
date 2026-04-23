# TASK-00013-05 config lint / dry-run 設計確定レビュー

- Status: done
- Role: reviewer
- Parent: TASK-00013
- Related IDs: REQ-00001, FUN-00402, FUN-00404, FUN-00405, FUN-00406, FUN-00407, CLI-00105, CLI-00109, CLI-00110, CLI-00111, CLI-00308, NFR-00302, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00013-01 の設計変更を確認し、`config lint` / `config dry-run` の仕様が実装着手条件を満たすかを判定する。あわせて、既存 `check` / `system-probe` と新 public surface の責務境界に矛盾がないかを確認する。

## 完了条件

- TASK-00013-01 の成果が実装に十分な粒度で確定している。
- `check` / `system-probe` / `config lint` / `config dry-run` の責務境界が矛盾なく整理されている。
- docs/design の TASK-00013 起因の追記に、未確定の名称や責務が既定仕様として混入していない。
- 差し戻し事項があれば、対象ファイルと論点を明記している。

## スコープ外

- `config lint` / `config dry-run` 実装そのもの
- README 更新
- 最終レビュー

## 進捗ログ

- 2026-04-23 project-master: 起票。programmer 着手前に reviewer の設計確認を挟むため追加
- 2026-04-23 reviewer: TASK-00013-01 と対象 docs/requirements, docs/design, 現行 CLI / Configuration Loader の責務境界を確認。`check` / `system-probe` / `config lint` / `config dry-run` の責務、`config lint` の単一ファイル入力境界、`config dry-run` の CLI-00308 と代表 1 Case 境界はいずれも整合しており、docs/design に未確定事項や実装シグネチャ混入は見当たらなかった。`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK。programmer 着手可と判定。

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

- progress/solution-architect/TASK-00013-01-design-config-lint-dry-run.md
- docs/requirements/02-functional.md
- docs/design/02-components.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- src/local_llm_benchmark/cli/main.py
- src/local_llm_benchmark/config/loader.py

### 発見事項

- 観点 1: 合格。`check` は既存互換の静的整合性確認、`system-probe` は host/provider/model の横断観測、`config lint` は利用者向け主導線の静的検証、`config dry-run` は Run 設定起点の個別 preflight として、[docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) で矛盾なく整理されている。現行 [src/local_llm_benchmark/cli/main.py](src/local_llm_benchmark/cli/main.py) の `check` / `system-probe` 実装責務とも整合する。
- 観点 2: 合格。`config lint` の主入力は「設定ディレクトリ全体または単一設定ファイル」で統一され、単一ファイル対象を Task Profile / Model Candidate / Provider / Run / Comparison に限定する点、補助設定ソースは「明示指定または標準配置から導出できる範囲のみ」とする点、解決不能時は検証省略ではなく configuration error にする点が [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md) と [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md) で一致している。
- 観点 3: 合格。`config dry-run` は静的読込失敗と補助設定不足を CLI-00303、provider 到達不可・指定 model 未解決・代表 1 Case の prompt 組立不可を CLI-00308 と分離しており、完了したが Run 前 NG を返す preflight として妥当である。代表 1 Case までに留め、実推論・採点・Result Store 書込・host facts 収集を責務外に置く境界も [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) で一致している。
- 観点 4: 合格。対象 docs/design には実装クラス名・関数シグネチャ・未確定 TODO の混入は見当たらない。`config dry-run` での代表 Case 選択や prompt 組立は概念責務の範囲に留まり、programmer の実装方法を過度に拘束していない。`MMDC_REQUIRED=1 bash scripts/verify.sh` の `check_no_implementation_leak.py` も OK。
- 観点 5: 合格。solution-architect task が列挙した正本 docs と現行 CLI / Loader の責務を合わせると、programmer は `config lint` の単一ファイル / 設定ディレクトリ両対応、`config dry-run` の Run 設定起点 preflight、CLI-00308 の実装へ着手できる粒度に達している。追加設計差し戻しは不要。

### 直接修正した範囲

- 本 reviewer task の Status、Related IDs、進捗ログ、レビュー記録を更新

### 差し戻し事項

- なし

### ユーザー報告可否

- 可。TASK-00013-01 はこのまま programmer 実装着手に進めてよい。