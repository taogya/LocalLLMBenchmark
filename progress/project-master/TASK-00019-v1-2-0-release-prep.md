# TASK-00019 v1.2.0 リリース準備

- Status: done
- Role: project-master
- Related IDs: REQ-00001, NFR-00001, NFR-00302, NFR-00501, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408, FUN-00409, FUN-00410, CLI-00109, CLI-00110, CLI-00111, CLI-00112, CLI-00113, CLI-00114, PROG-00103
- 起票日: 2026-04-24
- 完了日: 2026-04-24
- 対象バージョン: v1.2.0

## 目的

v1.2.0 の機能追加 (system-probe / config lint / config dry-run / provider preparation CLI) がそろったため、リリース前チェックを実施し、利用者向けドキュメントと release artifact 上の version 表記を v1.2.0 として整備する。README の section 見出しに残る旧 version 表記も、このタイミングで利用者向けに自然な形へそろえる。

## 完了条件

- README.md が v1.2.0 の公開面と主導線を反映し、`最短手順` と `既知の制約` の見出し version 表記が整理されている。
- CHANGELOG.md に 2026-04-24 付の v1.2.0 セクションが追加され、主要追加と既知の制約が利用者向けに要約されている。
- `docs/development/release-criteria.md` が v1.2.0 受入基準として読める状態に更新されている。
- package version と release artifact 上の version 表記 (`pyproject.toml`、必要な user-facing 表示) が 1.2.0 に更新されている。
- リリース前チェック (`verify.sh`、関連テスト、必要な smoke 観点) が実施され、結果が reviewer task に記録されている。

## スコープ外

- Git tag 作成 / push
- GitHub Release 作成
- 新機能の追加実装

## 委譲計画

- TASK-00019-01 docs-writer: README / CHANGELOG の v1.2.0 リリース向け更新と見出し整合
- TASK-00019-02 solution-architect: `docs/development/release-criteria.md` を v1.2.0 受入基準へ更新
- TASK-00019-03 programmer: package version と user-facing version 表記を 1.2.0 に更新
- TASK-00019-04 reviewer: リリース前チェックと成果物の最終確認

## 子 task

- TASK-00019-01 docs-writer: README / CHANGELOG v1.2.0 更新
- TASK-00019-02 solution-architect: v1.2.0 release-criteria 更新
- TASK-00019-03 programmer: package version 1.2.0 反映
- TASK-00019-04 reviewer: v1.2.0 リリース前チェック

## 進捗ログ

- 2026-04-24 project-master: 起票。README には `使い方の概観 (v1)` と並んで `最短手順 (v1.0.0)` / `既知の制約 (v1.0.0)` が残っており、CHANGELOG は 1.1.0 まで、`docs/development/release-criteria.md` は v1.0.0 題名のまま、`pyproject.toml` は `1.0.0`、CLI help / package docstring にも v1.0.0 表記が残っていることを確認した。
- 2026-04-24 project-master: ユーザー確認により、今回のリリース対応は docs だけでなく package version 反映まで含め、リリース日を 2026-04-24 として進める方針を確定した。
- 2026-04-24 docs-writer: TASK-00019-01 review-pending。README の `最短手順` / `既知の制約` 見出しから version 表記を外し、主導線を `provider status` → `model pull` → `model warmup` → `system-probe` → `config lint` → `config dry-run` → `run` に整理した。CHANGELOG には 2026-04-24 付の [1.2.0] を追加し、provider preparation CLI と preflight CLI を利用者向けに要約した。
- 2026-04-24 solution-architect: TASK-00019-02 review-pending。`docs/development/release-criteria.md` の題名・冒頭・機能要件表・smoke 観点表を v1.2.0 基準へ更新し、provider preparation CLI と preflight CLI の release smoke 観点を追加した。
- 2026-04-24 programmer: TASK-00019-03 review-pending。`pyproject.toml` の package version / description、CLI help、package docstring を 1.2.0 に更新し、release artifact 上の version 表記整合を反映した。
- 2026-04-24 reviewer: TASK-00019-04 review-pending。初回リリース前チェックで、solution-architect task の Related IDs に OOS が残り `verify.sh` が 9/10 だったこと、および `src/local_llm_benchmark.egg-info/PKG-INFO` が 1.0.0 のまま stale metadata だったことを blocker として差し戻した。
- 2026-04-24 solution-architect: TASK-00019-02 review-pending。reviewer 指摘を受け、自 task の Related IDs から OOS を除去して verify blocker を解消した。
- 2026-04-24 programmer: TASK-00019-03 review-pending。`src/local_llm_benchmark.egg-info/PKG-INFO` の Version / Summary と README 由来 metadata を 1.2.0 に同期し、stale packaging metadata を解消した。
- 2026-04-24 reviewer: TASK-00019-04 done。focused recheck で blocker 解消を確認し、`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK、`tests.test_cli_phase3` 31 tests OK、CLI help と package docstring の 1.2.0 表記整合を確認した。
- 2026-04-24 docs-writer: TASK-00019-01 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 solution-architect: TASK-00019-02 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 programmer: TASK-00019-03 done。reviewer 合格を受けて完了反映した。
- 2026-04-24 project-master: 子 task 完了とリリース前チェック通過を確認し、TASK-00019 を done に更新した。Git tag / GitHub Release 作成はスコープ外としてユーザーへ引き渡す。
