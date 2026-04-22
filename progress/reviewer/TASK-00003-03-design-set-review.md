# TASK-00003-03 設計セット最終確認

- Status: done
- Role: reviewer
- Parent: TASK-00003
- Related IDs: REQ-00001, ARCH-00001, PROG-00103

## 目的

TASK-00003-01 / TASK-00003-02 の成果物を含む上位設計セット全体を確認し、実装着手の前提が整っているかを判定する。

## 確認観点

- 中心目的 (REQ-00001) からの逸脱がないか
- 新規ドキュメントが既存 (`docs/requirements/`, `docs/design/01-04`, `docs/development/`) と矛盾しないか
- 新 ID (`CLI-` `CFG-` `PVD-` `SCR-`) が traceability ルール通りに採番・参照されているか
- README のリンクが網羅され、リンク切れがないか
- 設計書が実装と密になる具体記述 (クラス名・関数シグネチャ等) を含んでいないか
- 実装に着手可能な粒度になっているか (programmer が次の TASK を切れる状態か)

## 完了条件

- 上記観点の確認結果が `progress/reviewer/` の本 task 本文に記録されている
- ユーザー報告可否を明記
- 軽微な修正は直接実施、それ以外は project-master に差し戻し

## 着手条件

- TASK-00003-01 と TASK-00003-02 が `review-pending` または `done`

## 確認対象

- 新規/更新: `docs/design/05-cli-surface.md`, `docs/design/06-configuration-sources.md`, `docs/design/07-provider-contract.md`, `docs/design/08-scoring-and-ranking.md`, `docs/development/environment.md`, `docs/development/release-criteria.md`, `docs/development/traceability.md`, `.github/instructions/traceability.instructions.md`, `README.md`
- 整合確認: `docs/requirements/01-04`, `docs/design/01-04`, `docs/development/roles.md`, `docs/development/progress.md`

## 観点ごとの所見

1. 中心目的 (REQ-00001): 逸脱なし。05〜08 の全文書が冒頭で REQ-00001 を関連 ID に列挙し、ユーザーが自分の PC・用途で最適モデルを選ぶ目的に直結する記述に絞られている。release-criteria.md も v1.0.0 範囲を REQ-/FUN-/NFR- 単位で fold しており逸脱なし。
2. 既存との整合: 参照している既存 ID (DAT-00104/00105/00106/00201, FLW-00101/00102, COMP-00001〜00009, ARCH-00003/00005/00006/00303 ほか) はすべて出典文書に実在することを `grep_search` で確認。用語・依存方向 (Presentation → Orchestration → Measurement → Configuration & Storage) も逆転なし。05-cli-surface.md の `partial-failure` (CLI-00305) と FUN-00204 / FLW-00101 の関係は妥当。
3. 新 ID 採番: 5 桁 0 埋め・単調増加・カテゴリ内一意。`docs/development/traceability.md` と `.github/instructions/traceability.instructions.md` の双方に CLI-/CFG-/PVD-/SCR- が同一定義で追記済み。意味変更や欠番の再利用なし。TRC-00101〜00104 のルールに沿って、新 ID は根拠となる FUN-/NFR-/COMP- を本文で参照している。
4. README リンク: 関連ドキュメント節は新規 6 件を含めて網羅。リンクテキストとパスが一致しリンク切れなし。「使い方の概観」末尾と v1.0.0 ロードマップ末尾に新文書への導線あり。
5. 実装具体への踏み込み: 関数シグネチャ・クラス名・実装ライブラリ名は本文に出現せず、05-cli-surface.md 冒頭の「argparse / click 等には踏み込まない」という除外宣言のみ。設計確定 → 実装の順序 (PROG-00103) を阻害する記述はない。
6. 実装着手可能性: CLI サブコマンド ID と FUN-/FLW-/COMP- の対応表 (CLI-00101 系)、CFG- ファイル種別と所有者、PVD- 標準リクエスト/レスポンス/失敗種別、SCR- scorer 語彙とランキング算出が概念粒度で揃っている。programmer 側で COMP- 単位の実装 task を切れる状態。
7. progress 運用: 本 task と TASK-00003-01/02 はいずれも TASK-NNNNN-SS 形式、必須項目 (Status/Role/Parent/Related IDs/目的/完了条件/着手条件/進捗ログ) を満たす。状態遷移も `open → in-progress → review-pending → done` の規定どおり。

## 直接修正した範囲

- `README.md` の「関連ドキュメント」: `06-configuration-sources.md` の説明を「設定ソースと優先順位」から「設定ソースと BYO データ分離」に修正 (本文 06 が優先順位を扱わないため)。

## 差し戻し事項

なし。設計内容に踏み込む修正は不要。

## 残課題 (ユーザー報告外, 後続 task 起票で対応)

- ランキング統合軸の重み既定値 (SCR-00605/00606 = 0.7/0.3) は v1 smoke 検証後に再評価する旨を release-criteria 検証 task に含めること (TASK-00003-01 の残課題と一致)。
- v1.0.0 受入のための単一検証 task は project-master が別途起票する必要あり (release-criteria.md にも明記済み)。

## ユーザー報告可否

Yes。設計セットは中心目的・既存設計・ID 体系・実装着手粒度のすべてを満たし、軽微な README 表記不一致のみ直接修正済み。差し戻しなしで Status を `done` に更新。

