# TASK-00004-02 README 更新 (1 Run = 1 Model 反映)

- Status: review-pending
- Role: docs-writer
- Parent: TASK-00004
- Related IDs: REQ-00001..REQ-00009

## 目的

TASK-00004-01 の設計改訂を README に反映する。

## 成果物

- README.md の以下を更新
  - 「使い方の概観 (v1)」: 「比較したい候補モデルを登録 → ベンチを実行」を「1 モデル単位で Run を実行 → 複数 Run を Comparison で束ねる」流れに修正
  - ロードマップ v1.0.0: 「複数モデル比較 = Comparison」と明示
  - 「何を見せるか」: ランキングは Comparison の成果物である旨を反映
  - 関連ドキュメントのリンクは TASK-00004-01 で増減した場合のみ追従

## 制約

- 設計内容の意味を変えない (TASK-00004-01 の確定内容に従う)
- `docs/requirements/` `docs/design/` `docs/development/` 配下を編集しない
- 既存リンクの断は起こさない (リンク切れチェックを目視で実施)

## 着手条件

- TASK-00004-01 が `review-pending` または `done`

## 完了条件

- README に新方針 (1 Run = 1 Model + Comparison) が反映
- ロードマップが整合
- Status を `review-pending` に更新

## 進捗ログ

- 2026-04-19: README.md を更新。
  - 「何を見せるか」: ランキングを「複数 Run を束ねた **Comparison** から導出される **モデルランキング**」に書き換え。
  - 「使い方の概観 (v1)」: 4 ステップを「task profile 登録 → provider 上に候補モデル用意 → モデルごとに Run (1 Run = 1 Model) → Comparison で束ねてランキング表示」に再構成。
  - ロードマップ v1.0.0: 「**Comparison によるモデルランキング表示** (品質軸 / 速度軸)」へ修正。
  - 「関連ドキュメント」: 設計側のファイル増減なし、リンク断なしを目視確認 (リンク変更なし)。
- 参照した一次情報:
  - [docs/design/03-data-model.md](../../docs/design/03-data-model.md) (DAT-00008 Run / DAT-00009 Comparison)
  - [docs/design/02-components.md](../../docs/design/02-components.md) (COMP-00011 Run Comparator)
  - [docs/design/04-workflows.md](../../docs/design/04-workflows.md) (FLW-00006 Comparison 作成フロー)
  - [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) (CLI-00106/00107/00108)
  - [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md) (FUN-00207/00307/00308)
  - 親 task: [TASK-00004-01](../solution-architect/TASK-00004-01-design-rewrite.md)
- 残課題: なし。

