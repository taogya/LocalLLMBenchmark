# TASK-00019-02 v1.2.0 release-criteria 更新

- Status: done
- Role: solution-architect
- Parent: TASK-00019
- Related IDs: REQ-00001, FUN-00105, FUN-00402, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408, FUN-00409, FUN-00410, NFR-00001, NFR-00002, NFR-00302, NFR-00501, PROG-00103
- 起票日: 2026-04-24

## 目的

`docs/development/release-criteria.md` を v1.2.0 の受入基準として更新し、v1.0.0 題名のまま残っている release 文書を現行スコープに合わせる。既に確定している v1.2.0 の要件・設計・進捗を正本として、release smoke 観点を整理する。

## 完了条件

- `docs/development/release-criteria.md` が v1.2.0 リリース受入基準として読める題名と本文に更新されている。
- v1.2.0 で追加された公開面と release smoke 観点が過不足なく反映されている。
- 未対応事項と後段リリース境界が、現行 OOS / roadmap と矛盾しない。
- docs/development に未確定情報や実装シグネチャを持ち込んでいない。

## スコープ外

- README / CHANGELOG 更新 (TASK-00019-01)
- package version 更新 (TASK-00019-03)
- リリース前チェック最終判定 (TASK-00019-04)

## 進捗ログ

- 2026-04-24 project-master: 起票。`docs/development/release-criteria.md` は v1.2.0 の ID 群を含むが題名と本文の基準時点が v1.0.0 のまま残っているため、release 文書としての整合を更新する必要がある。
- 2026-04-24 solution-architect: `docs/requirements/02-functional.md`、`docs/requirements/04-out-of-scope.md`、`docs/design/04-workflows.md`、`docs/design/05-cli-surface.md`、`docs/design/06-configuration-sources.md`、`docs/design/07-provider-contract.md`、`progress/project-master/TASK-00012-v1-2-0-system-probe.md`、`progress/project-master/TASK-00013-v1-2-0-config-lint-dry-run.md`、`progress/project-master/TASK-00014-v1-2-0-provider-cli-warmup.md` を確認し、v1.2.0 の現行 public surface と OOS 境界を再確認した。
- 2026-04-24 solution-architect: `docs/development/release-criteria.md` を v1.2.0 基準へ更新。題名・冒頭・smoke 観点を現行版へそろえ、`provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run` の受入観点を追加し、旧 v1.0.0 固有表現と future v1.2.0 行を整理した。後段リリース境界は README ロードマップと矛盾しないよう `v2.0.0` と `版未定` に再整理した。
- 2026-04-24 solution-architect: task を review-pending に更新。reviewer には v1.2.0 の公開面反映漏れ、および OOS-00006 / OOS-00012 を用いた release 境界表現が現行正本と整合するかを重点確認依頼する。
- 2026-04-24 solution-architect: reviewer 差し戻し対応として active task の `Related IDs:` から OOS-00006 / OOS-00012 を除外し、Status は review-pending のまま reviewer 再確認待ちとした。
- 2026-04-24 solution-architect: reviewer task `TASK-00019-04` が `done` / 合格になったことを確認し、`docs/development/release-criteria.md` 反映の reviewer 確認完了として本 task の Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- v1.2.0 の現行公開面 (`provider status` / `model pull` / `model warmup` / `system-probe` / `config lint` / `config dry-run`) が release-criteria の機能要件表と smoke 観点表の両方に過不足なく反映されているか。
- `docs/development/release-criteria.md` が OOS-00006 / OOS-00012 を境界として扱い、README ロードマップの v2.0.0 と矛盾しない future 境界になっているか。