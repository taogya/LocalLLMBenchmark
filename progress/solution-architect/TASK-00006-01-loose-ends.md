# TASK-00006-01 残課題対応 (DAT-00109 強化、SCR 注記、release-criteria smoke チェックリスト)

- Status: done
- Role: solution-architect
- Parent: TASK-00006
- Related IDs: DAT-00109, SCR-00806, SCR-00807, NFR-00101, FUN-00308, FUN-00309

## 目的

実装着手前の小規模設計補完を 1 task で対応する。

## 成果物

### 1. DAT-00109 の強化

- 対象: `docs/design/03-data-model.md` の DAT-00109
- 現状: `Comparison は同一 TaskProfile セットの Run を束ねる` 程度の記述
- 改訂方針: Comparison は **最小 2 件以上の Run** を束ねることを必須とする (1 件では「比較」の意味が成立しないため)
- supersede の必要はない (不変条件の追加は意味変更ではなく強化のため、本文に追記でよい)。ただし「最小 2 件未満の場合 Run Comparator はエラーとして扱う」旨を明記
- 関連: FUN-00308, FUN-00309, FLW-00006

### 2. SCR-00806 / SCR-00807 の注記

- 対象: `docs/design/08-scoring-and-ranking.md` の SCR-00806 (`w_quality=0.7`), SCR-00807 (`w_speed=0.3`) 該当行
- 改訂方針: 各 ID の本文末尾に「**この既定値は v1 smoke 後に再評価する**」旨を 1 行で追記
- 採番: 不要 (注記の追加であり意味変更ではない)

### 3. release-criteria.md に smoke 観点チェックリストを追記

- 対象: `docs/development/release-criteria.md`
- 現状: 受入基準 (満たすべき FUN-/NFR- ID) は記載済み
- 追記内容: 「v1.0.0 smoke 観点チェックリスト」セクションを新設
  - 各受入観点に対して「smoke で何を観察すれば満たしたと判断できるか」を 1 行で示す
  - 例: FUN-00207 → 「`run` サブコマンドで 1 モデル指定 + 1 Task Profile + n=3 で完走し、Run 識別子が返る」
  - 観点は実装フェーズで TASK-NNNNN-XX として個別 task 化される前提
- ID 採番: 不要 (運用補足)

## 制約

- 設計内容の意味は変えない (強化と注記のみ)
- 実装に踏み込んだ記述 (クラス名・関数シグネチャ等) を入れない
- 影響範囲を確認: DAT-00109 強化に伴い、参照元 (FLW-00006 注、CFG-00207 等) との整合を点検

## 完了条件

- 上記 3 件が反映されている
- 関連 ID への影響を確認済み
- `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行して全 OK を確認 (本 task で reviewer 役割を兼ねる)
- Status を `review-pending` に更新

## 進め方

1. Status を `in-progress` に
2. 上記 3 件を反映
3. 検証 (verify.sh) を実行
4. 進捗ログに変更点と検証結果を記録し `review-pending` に

## 進捗ログ

- 2026-04-19 solution-architect: 3 件を反映。
  - `docs/design/03-data-model.md`: DAT-00109 を「最小 2 件以上の Run + 同一 TaskProfile セット、違反時 Run Comparator がエラー」に強化。整合のため DAT-00108 を「2 件以上保持」に揃え (1 件以下は Comparison 生成拒否)。
  - `docs/design/04-workflows.md`: FLW-00006 シーケンスに「Run 数下限検査 (DAT-00108 / DAT-00109)」を追加し、注記に 2 件未満エラーを明記。
  - `docs/design/06-configuration-sources.md`: CFG-00207 必須項目を「2 件以上の Run 識別子集合」に更新、CFG-00506 検証項目も 2 件以上に追従。
  - `docs/design/08-scoring-and-ranking.md`: SCR-00806 / SCR-00807 既定値欄に「v1 smoke 後に再評価」を 1 行追記。
  - `docs/development/release-criteria.md`: 末尾に「## v1.0.0 smoke 観点チェックリスト」を新設し、FUN-/NFR- 各 ID に smoke 観察項目を 1 行ずつ列挙。
- 2026-04-19 solution-architect: 検証 (verify.sh) は本セッションでターミナル実行手段が無いため未実行。Status は `review-pending` とし、reviewer または project-master 側で `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行して結果を本ログに追記してください。
- 2026-04-19 reviewer: `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行し、10 種すべて OK を確認。観点 (意味変更なし / 実装具体なし / ID トレーサビリティ維持 / DAT-00108・DAT-00109 参照整合 / smoke チェックリストが FUN-・NFR- 受入基準と 1:1 対応) すべて合格。`done` に更新。
