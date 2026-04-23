# TASK-00018 docs/design 確定情報運用整備

- Status: done
- Role: project-master
- Related IDs: ROLE-00001, ROLE-00002, PROG-00103
- 起票日: 2026-04-23
- 完了日: 2026-04-23

## 目的

`docs/design/` に未確定情報が混入していないかを監査し、設計書には確定した設計情報のみを書く運用を明文化する。未確定事項や将来候補は `progress/` や README ロードマップへ逃がし、設計書の正本性を維持する。

## 完了条件

- docs/design にある未確定情報の候補が分類され、対象ファイルと論点が列挙されている。
- 「設計書には確定した設計情報のみを書く」ルールが既存ルール群に反映されている。
- 未確定情報と判定した項目について、設計書から除去・移送・確定のいずれで扱うかの方針が決まっている。
- 必要な後続 task が起票されている。

## スコープ外

- 実装コードの変更
- README ロードマップ自体の改訂

## 委譲計画

- TASK-00018-01 solution-architect: docs/design の未確定情報候補を監査し、設計書に残すべき確定情報と progress 側へ逃がすべき情報を分類する
- TASK-00018-02 reviewer: 監査結果とルール追加の妥当性を確認する

## 子 task

- TASK-00018-01 solution-architect: docs/design 未確定情報監査
- TASK-00018-02 reviewer: docs/design 未確定情報監査の確認

## 進捗ログ

- 2026-04-23 project-master: 起票。候補として [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md) の「具体形式は実装で確定する」系記述、[docs/design/04-workflows.md](../../docs/design/04-workflows.md) / [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) / [docs/design/06-configuration-sources.md](../../docs/design/06-configuration-sources.md) / [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) の「将来の config lint / dry-run」記述、[docs/design/01-architecture.md](../../docs/design/01-architecture.md) の将来拡張節を確認
- 2026-04-23 project-master: 既存ルールには「実装に踏み込まない」はあるが、「未確定情報を設計書へ書かない」は無かったため、[.github/instructions/documentation.instructions.md](../../.github/instructions/documentation.instructions.md) に明示ルールを追加
- 2026-04-23 solution-architect: TASK-00018-01 review-pending。`docs/design/01-architecture.md` は確定済み拡張境界として維持、`docs/design/04-workflows.md` / `05-cli-surface.md` / `06-configuration-sources.md` / `07-provider-contract.md` の未確定な将来 public surface 名を除去、`docs/design/02-components.md` / `03-data-model.md` を含む同種表現も整理
- 2026-04-23 reviewer: TASK-00018-02 done。未確定情報候補の分類、ルール追加、責務境界維持は妥当と判定し、`MMDC_REQUIRED=1 bash scripts/verify.sh` 10/10 OK を確認
- 2026-04-23 solution-architect: TASK-00018-01 done。reviewer 合格を受けて監査 task を完了化
- 2026-04-23 project-master: 監査・ルール追加・review 完了を確認し、TASK-00018 を done に更新
