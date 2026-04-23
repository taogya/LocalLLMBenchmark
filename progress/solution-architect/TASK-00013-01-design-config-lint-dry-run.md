# TASK-00013-01 config lint / dry-run 仕様と関連設計確定

- Status: done
- Role: solution-architect
- Parent: TASK-00013
- Related IDs: REQ-00001, FUN-00105, FUN-00402, FUN-00406, FUN-00407, CLI-00105, CLI-00109, CLI-00110, CLI-00111, CLI-00308, FLW-00003, FLW-00007, FLW-00008, FLW-00009, CFG-00604, CFG-00605, CFG-00606, CFG-00607, PVD-00406, NFR-00302, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00013 で追加する `config lint` / `config dry-run` について、現行 `check` / `system-probe` との責務境界、利用者向け public surface、入力単位、終了コード、既存 Configuration Loader / Provider Adapter / Run 計画組立との接続点を先に確定し、programmer が迷わず実装できる状態にする。

## 完了条件

- `check` / `system-probe` / `config lint` / `config dry-run` の責務境界が、現行 trunk と docs/design の両方に矛盾なく整理されている。
- `config lint` の入力単位 (単一ファイル / 設定ディレクトリ / 両対応) と、Comparison / Run / TaskProfile / Provider の検証導線が確定している。
- `config dry-run` の入力、実施範囲、`system-probe` 再利用境界、1 case の prompt 組立までの扱いが確定している。
- 必要な ID (FUN- / CLI- / CFG- / FLW- / PVD- など) の追加または更新要否が整理され、関連する docs/ の更新対象が列挙されている。
- programmer / docs-writer / reviewer に引き継ぐ影響範囲と確認観点が列挙されている。

## スコープ外

- `config lint` / `config dry-run` の実装とテスト (TASK-00013-02)
- README 更新 (TASK-00013-03)
- 最終レビュー (TASK-00013-04)

## 設計対象

- 利用者向け public surface と既存 `check` / `system-probe` との互換方針
- `config lint` / `config dry-run` の入力、出力、終了状態
- 既存 Configuration Loader、Run 計画組立、Provider Adapter、sample config との接続点

## 設計判断

### 1. public surface と互換方針

| 面 | 結論 |
| --- | --- |
| `system-probe` | host facts、provider reachability、model availability を扱う横断観測面として維持する |
| `config lint` | 利用者向け主導線の静的 validation 面として追加する。単一ファイルと設定ディレクトリの両方を主入力にできる |
| `config dry-run` | Run 設定起点の preflight 面として追加する。`system-probe` を置き換えず、Run 実行前の個別確認に限定する |
| `check` | 既存互換面として維持する。設定ディレクトリ / Comparison 設定の静的整合性確認に責務を固定し、利用者向け主導線では `config lint` を優先する |

利用者向け導線は `system-probe` → `config lint` → `config dry-run` → `run` とする。`check` の意味は変更せず、後方互換の public surface として残す。

### 2. `config lint` の両対応入力

- 主入力は「設定ディレクトリ全体」または「単一設定ファイル」のどちらか 1 つとする。
- 単一ファイルとして扱う対象は Task Profile 定義、Model Candidate 定義、Provider 接続情報、Run 設定、Comparison 設定に限る。
- 単一ファイルが相互参照を持つ場合は、明示指定または標準配置から導出できる補助設定ソースだけを読み、解決できない補助ソースは検証省略ではなく設定エラーとして報告する。
- provider 通信は行わず、静的整合性と Result Store 参照整合性までを扱う。

### 3. `config dry-run` の責務

- 主入力は Run 設定とし、Task Profile / Model Candidate / Provider 定義を補助設定ソースとして解決する。
- 出力は JSON 一次、Markdown 派生とし、最小セクションは `run`, `probe`, `prompt_check`, `summary` の 4 つに固定する。
- 終了コードは「静的読込失敗や補助設定不足は configuration error」「provider 到達不可 / 指定 model 未解決 / 代表 1 Case の prompt 組立不可は dry-run-negative」で分ける。
- prompt 組立は Run の実行順から決まる代表 1 Case のみを対象とし、実推論、採点、Result Store 書込、host facts 収集は責務外とする。

### 4. programmer / reviewer の正本

- programmer の正本は [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) とする。
- reviewer は次を重点確認する。
	- `check` / `system-probe` / `config lint` / `config dry-run` の責務交差が無いこと
	- `config lint` の単一ファイル / 設定ディレクトリ入力境界が docs 間で一致していること
	- `config dry-run` が host inventory や実推論に広がらず、代表 1 Case の prompt 組立に止まっていること

## 影響範囲

- [docs/requirements/02-functional.md](docs/requirements/02-functional.md): FUN-00406 / FUN-00407 を追加
- [docs/design/02-components.md](docs/design/02-components.md): CLI Entry / Configuration Loader / Provider Adapter の責務境界を更新
- [docs/design/04-workflows.md](docs/design/04-workflows.md): FLW-00008 / FLW-00009 と主導線を追加
- [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md): CLI-00110 / CLI-00111 / CLI-00308 と診断系サブコマンド境界を追加
- [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md): CFG-00604〜00607 を追加し、単一ファイル入力と dry-run 補助ソースを定義
- [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md): 非推論 probe の再利用先を `config dry-run` まで明文化

## 残課題

- なし

## 進捗ログ

- 2026-04-23 project-master: 起票。設計確定を実装着手の前提とするため、public surface と責務境界の確定を先行依頼
- 2026-04-23 solution-architect: Status を `in-progress` として着手。関連ルール、TASK-00013 親 task、TASK-00012 の設計・レビュー記録、docs/requirements / docs/design、現行 `src/local_llm_benchmark/cli/main.py` と `src/local_llm_benchmark/config/loader.py` を確認し、`check` は静的検証、`system-probe` は動的観測に限定されていることを確認した。
- 2026-04-23 solution-architect: [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) を更新。FUN-00406 / FUN-00407, FLW-00008 / FLW-00009, CLI-00110 / CLI-00111 / CLI-00308, CFG-00604〜00607 を採番し、`check` / `system-probe` / `config lint` / `config dry-run` の責務境界、`config lint` の単一ファイル / 設定ディレクトリ両対応、`config dry-run` の最小出力と終了コードを確定した。
- 2026-04-23 solution-architect: 完了条件を満たしたため Status を `review-pending` に更新。programmer は CLI / workflow / configuration / provider 契約の 4 文書を合わせて参照し、reviewer は単一ファイル入力境界、`system-probe` 非置換、代表 1 Case prompt 組立の範囲を重点確認する。
- 2026-04-23 solution-architect: [progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md](progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md) の合格、差し戻しなしを確認。reviewer 合格を受けて本 task の Status を `done` に更新し、設計確定とした。

## レビュー記録 (reviewer 用)

- 2026-04-23 reviewer: [progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md](progress/reviewer/TASK-00013-05-review-config-lint-dry-run-design.md) で合格。差し戻し事項なし。設計確定として programmer 着手可。