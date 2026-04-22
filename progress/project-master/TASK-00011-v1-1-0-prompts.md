# TASK-00011 v1.1.0 コンフィグ生成・選定支援プロンプト群

- Status: done
- Role: project-master
- Related IDs: REQ-00001
- 起票日: 2026-04-22
- 完了日: 2026-04-22
- 対象バージョン: v1.1.0

## 目的

`.github/prompts/` 配下に askQuestions ベースの対話型プロンプトを追加し、利用者がヒアリングを通じて
コンフィグ作成とモデル選定を支援できるようにする。
コードは触らず prompt のみで価値を出す非破壊スコープ。

## 完了条件

- 以下 2 種の prompt が `.github/prompts/` 配下に存在し、VS Code Copilot Chat から呼び出せる:
  - **コンフィグ生成プロンプト**: TaskProfile / Provider / Run / Comparison の TOML を askQuestions で項目を埋めながら個別生成する。出力先フォルダもヒアリングし、sample config の上書きを避ける導線を持つ。
  - **model-recommender プロンプト**: provider を先にヒアリングし、その provider で利用可能なモデル候補を Web 情報から収集して提示する。PC スペック (CPU / メモリ / GPU / OS) と用途 (要約 / 分類 / 短文 QA など) も踏まえ、候補ごとの特徴と選定理由を返す。
- 各 prompt の冒頭に目的・前提・出力先を記載 (利用者視点)。トレース ID は出さない。
- README ロードマップ v1.1.0 区分の記述と整合。
- CHANGELOG に未リリース変更として v1.1.0 の prompt 追加内容が記載されている。

## スコープ外

- 診断レポート生成 prompt (既存 `report` 出力と将来の Web UI へ寄せる)
- prompt 品質採点ウィザード (今回ヒアリングで不採用)
- コンフィグ diff/乗り換えウィザード (今回ヒアリングで不採用)
- 新規 CLI サブコマンド (v1.2.0 以降)
- `release-criteria.md` の v1.1.0 ID 単位展開 (着手時に solution-architect が追加)

## 想定委譲計画 (着手時に確定)

- solution-architect: prompt 仕様 (ヒアリング項目 / 出力 TOML スキーマとの対応 / 既存 sample との関係) を確定
- docs-writer: `.github/prompts/` 配下の prompt 本体を執筆
- reviewer: 利用者視点・トレース ID 非含有・出力 TOML が config loader で読めるかの整合確認

## 子 task

- TASK-00011-01 solution-architect: prompt 仕様確定
- TASK-00011-02 docs-writer: `.github/prompts/` 本体執筆
- TASK-00011-03 reviewer: prompt 仕様・文面・生成物整合の最終確認
- TASK-00011-04 docs-writer: CHANGELOG へ v1.1.0 未リリース変更を追記
- TASK-00011-05 reviewer: CHANGELOG 追記内容の最終確認

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (A + B + P3 採用) を踏まえ起票
- 2026-04-22 project-master: TASK-00011 を開始。`.github/prompts/` は未作成であること、`configs/model_registry/` 参照は現行 trunk に存在しないことを確認
- 2026-04-22 project-master: コンフィグ生成 prompt は 4 ファイル個別生成 + 出力先フォルダのヒアリング必須で確定。model-recommender は provider 先行ヒアリング + Web 情報参照方針へ更新
- 2026-04-22 project-master: 診断レポート prompt は v1.1.0 から外し、既存 `report` 出力と v2.0.0 Web UI 側へ寄せる方針で確定
- 2026-04-22 project-master: 親 task ファイル名を progress 規約 (`TASK-NNNNN-<slug>.md`) に合わせて正規化
- 2026-04-22 solution-architect: TASK-00011-01 done。`.github/prompts/config-generator.prompt.md` と `.github/prompts/model-recommender.prompt.md` の仕様を確定
- 2026-04-22 docs-writer: TASK-00011-02 done。`.github/prompts/` を新設し、2 prompt を追加
- 2026-04-22 reviewer: TASK-00011-03 done。prompt 内容・progress・verify.sh 10/10 OK を確認
- 2026-04-22 project-master: 親 task を done に更新
- 2026-04-22 project-master: ユーザー指摘により CHANGELOG 反映漏れを確認。親 task を再開し、TASK-00011-04 / TASK-00011-05 を追加
- 2026-04-22 docs-writer: TASK-00011-04 review-pending。`CHANGELOG.md` に `Unreleased` / `Added` を追加し、2 prompt の未リリース変更を反映
- 2026-04-22 reviewer: TASK-00011-05 done。CHANGELOG 追記は妥当、verify.sh 10/10 OK、差し戻しなしを確認
- 2026-04-22 docs-writer: TASK-00011-04 done。reviewer 合格を反映
- 2026-04-22 project-master: CHANGELOG 反映漏れ対応込みで親 task を再度 done に更新