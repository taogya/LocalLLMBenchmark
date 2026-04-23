# TASK-00014-01 provider status / model pull / model warmup 仕様と関連設計確定

- Status: done
- Role: solution-architect
- Parent: TASK-00014
- Related IDs: REQ-00001, FUN-00408, FUN-00409, FUN-00410, CLI-00112, CLI-00113, CLI-00114, CLI-00205, CLI-00309, FLW-00010, FLW-00011, FLW-00012, CFG-00608, CFG-00609, CFG-00610, PVD-00005, PVD-00108, PVD-00109, PVD-00110, PVD-00212, PVD-00213, PVD-00214, PVD-00215, PVD-00402, PVD-00406, PVD-00407, PVD-00408, PROG-00103
- 起票日: 2026-04-24

## 目的

TASK-00014 で追加する `provider status` / `model pull` / `model warmup` について、現行 `system-probe` / `config dry-run` との責務境界、利用者向け public surface、進捗表示、終了コード、既存 Provider Adapter / probe 基盤との接続点を先に確定し、programmer が迷わず実装できる状態にする。あわせて、現行 docs/design に残る「model pull / warm-up は責務外」という前提との不整合を解消する。

## 完了条件

- `provider status` / `model pull` / `model warmup` の責務境界が、現行 trunk と docs/design の両方に矛盾なく整理されている。
- `provider status` と既存 `system-probe` の関係、`model warmup` と既存 `config dry-run` の関係、`model pull` の責務境界が確定している。
- 進捗表示方針 (pull の進捗、warmup 完了表示、結果出力との分離) と終了コード方針が確定している。
- 必要な ID (FUN- / CLI- / FLW- / PVD- など) の追加または更新要否が整理され、関連する docs/ の更新対象が列挙されている。
- programmer / docs-writer / reviewer に引き継ぐ影響範囲と、reviewer が実機確認で見るべき観点が列挙されている。

## スコープ外

- `provider status` / `model pull` / `model warmup` の実装とテスト (TASK-00014-02)
- README 更新 (TASK-00014-03)
- 最終レビュー (TASK-00014-04)

## 設計対象

- `provider status` / `model pull` / `model warmup` の public surface、入力、出力、終了状態
- `system-probe` / `config dry-run` / Provider Adapter probe 契約との責務境界
- 既存 PVD-00402 / PVD-00406 と v1.2.0 スコープの整合

## 設計判断

### 1. `provider status` は `system-probe` の置き換えではなく、provider inventory の直接確認面とする

| 面 | 結論 |
| --- | --- |
| `provider status` | Provider 接続情報だけを入力に、起動状態、版情報、利用可能 model inventory を返す |
| `system-probe` | host facts と登録済み Model Candidate の横断観測に集中し、provider inventory の直接一覧面にはしない |

根拠:
- `system-probe` は CFG-00102 / CFG-00104 を入力にして host snapshot と Model Candidate 可用性を束ねる既存面であり、provider そのものの inventory 確認とは粒度が異なる。
- reviewer が provider 起動状態の切り分けを行うには、host facts や candidate cross-check を含まない単独面が必要である。

### 2. `model pull` は explicit acquisition とし、暗黙 pull を禁止する

- `model pull` は 1 件の provider と 1 件の model target を対象にする。
- `run` / `system-probe` / `config dry-run` / `model warmup` は pull を暗黙起動しない。
- OOS-00005 は OOS-00012 に supersede し、「暗黙 model pull の禁止」に縮退する。

### 3. `model warmup` は `config dry-run` と分離し、actual provider execution を 1 回だけ行う

| 面 | 結論 |
| --- | --- |
| `config dry-run` | Run 設定起点の read-only preflight。provider reachability、指定 model 解決、代表 1 Case の prompt 組立可否まで |
| `model warmup` | Provider / model target 起点の explicit preparation。command-scoped な最小 input を 1 回投げてロード状態へ寄せる |

根拠:
- `config dry-run` は actual provider execution を伴わないことが既存設計の要点であり、warmup を持ち込むと CLI-00308 の意味が崩れる。
- warmup 効果の実機確認は reviewer 観点に入るため、TaskProfile / Run 設定に依存しない独立面として扱う方が判定しやすい。

### 4. 進捗表示は stderr、正準結果は stdout に固定する

- `provider status` は進捗を持たず、negative issue のみを stderr に 1 行 1 件で出す。
- `model pull` / `model warmup` は進捗と開始 / 完了通知を stderr に出し、stdout には最終 JSON / Markdown のみを出す。
- 新しい negative 終了コードは `provider status` のみ追加し、`model pull` / `model warmup` の失敗は CLI-00304 runtime error を使う。

### 5. PVD-00402 / PVD-00406 は supersede で扱う

- PVD-00402 → PVD-00407: provider 起動 / 停止管理は引き続き対象外だが、`provider status` と `model pull` は explicit operation として対象化する。
- PVD-00406 → PVD-00408: read-only な status / probe と explicit preparation (`model pull` / `model warmup`) を分離し、暗黙 pull を禁止する。

## 影響範囲

- 正本更新: [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md), [docs/requirements/04-out-of-scope.md](../../docs/requirements/04-out-of-scope.md), [docs/design/02-components.md](../../docs/design/02-components.md), [docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md)
- 整合更新: [docs/development/environment.md](../../docs/development/environment.md), [docs/development/release-criteria.md](../../docs/development/release-criteria.md)
- programmer は上記 docs/design と docs/requirements を正本として実装着手する。
- docs-writer は README 更新時に、`provider status` / `system-probe`、`model warmup` / `config dry-run` の使い分けを利用者向けに短く説明する。

## reviewer 重点観点

- `provider status` が host facts や Model Candidate cross-check を持ち込まず、`system-probe` と責務交差していないこと
- `model warmup` が `config dry-run` を実質置換せず、actual provider execution を伴う独立面になっていること
- `model pull` の explicit 性が docs/requirements / docs/design / OOS で一致し、暗黙 pull 禁止が崩れていないこと
- PVD-00402 → PVD-00407、PVD-00406 → PVD-00408、OOS-00005 → OOS-00012 の supersede 連結が progress と docs 本文の両方で追えること
- reviewer 最終 task で warmup 有無の実機差分または warmup 完了後の状態改善を確認できる設計粒度になっていること

## 残課題

- なし

## 進捗ログ

- 2026-04-24 project-master: 起票。現行 docs/design では model pull / warm-up が責務外になっている一方、ユーザー確認により TASK-00014 で v1.2.0 へ取り込む方針が確定したため、設計差分の吸収を先行依頼する。
- 2026-04-24 project-master: ユーザー確認済み事項として、公開面は `provider status` / `model pull` / `model warmup` を新設し、reviewer による warmup 効果の実機確認を完了条件に含める。現行 trunk には `system-probe` / `config lint` / `config dry-run` が既にあるため、今回の設計は additive で既存面を壊さないことを前提とする。
- 2026-04-24 solution-architect: Status を `in-progress` として着手。関連ルール、親 task、TASK-00012 / TASK-00013 の設計差分、[docs/requirements/02-functional.md](../../docs/requirements/02-functional.md), [docs/requirements/04-out-of-scope.md](../../docs/requirements/04-out-of-scope.md), [docs/design/02-components.md](../../docs/design/02-components.md), [docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md), [docs/development/release-criteria.md](../../docs/development/release-criteria.md) を確認し、OOS-00005 / PVD-00402 / PVD-00406 の旧前提を supersede で扱う必要があると判断した。
- 2026-04-24 solution-architect: [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md), [docs/requirements/04-out-of-scope.md](../../docs/requirements/04-out-of-scope.md), [docs/design/02-components.md](../../docs/design/02-components.md), [docs/design/04-workflows.md](../../docs/design/04-workflows.md), [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md), [docs/development/environment.md](../../docs/development/environment.md), [docs/development/release-criteria.md](../../docs/development/release-criteria.md) を更新。FUN-00408〜00410、CLI-00112〜00114 / CLI-00205 / CLI-00309、FLW-00010〜00012、CFG-00608〜00610、PVD-00005 / PVD-00108〜00110 / PVD-00212〜00215 / PVD-00407〜00408、OOS-00012 を採番し、`provider status` / `model pull` / `model warmup` の責務境界、進捗ストリーム分離、explicit preparation 方針を設計へ反映した。supersede 対応は OOS-00005 → OOS-00012、PVD-00402 → PVD-00407、PVD-00406 → PVD-00408 とした。
- 2026-04-24 solution-architect: 完了条件を満たしたため Status を `review-pending` に更新。reviewer は `provider status` / `system-probe`、`model warmup` / `config dry-run` の責務境界、暗黙 pull 禁止、PVD supersede 連結、warmup 実機確認観点を重点確認する。
- 2026-04-24 solution-architect: [progress/reviewer/TASK-00014-05-review-provider-cli-warmup-design.md](../reviewer/TASK-00014-05-review-provider-cli-warmup-design.md) の `done` / 合格を確認したため、reviewer 合格反映として本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- 2026-04-24 solution-architect: reviewer 差し戻し対応。Related IDs から OOS-00005 / OOS-00012 を除外し、supersede の説明は本文と進捗ログに維持した。Status は reviewer 再確認待ちのため `review-pending` を継続。