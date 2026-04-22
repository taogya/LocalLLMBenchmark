# TASK-00010 v1.1.0 以降ロードマップ反映

- Status: done
- Role: project-master
- Related IDs: REQ-00001
- 起票日: 2026-04-20
- 完了日: 2026-04-20

## 目的

v1.0.0 リリース後のユーザー要望ヒアリング結果を [README.md](../../README.md) のロードマップ節に反映する。設計・実装は本 task では行わない (記述のみ)。

## ヒアリング結果 (採用機能)

- A: `.github/prompts` に askQuestions ベースのコンフィグ生成プロンプトを追加
- B: model-recommender prompt (PC スペック × 用途 → 推奨モデル選定支援)
- C: system-probe サブコマンド (CPU/メモリ/GPU/OS 自動取得)
- F: config lint / dry-run サブコマンド
- D: LM Studio / llama.cpp server 等のプロバイダ追加

## バージョン振り分け案

- **v1.1.0** (非破壊・prompt 追加のみ): A, B
- **v1.2.0** (非破壊・新サブコマンド追加): C, F
- **v2.0.0** (Provider Adapter 抽象再設計を伴うため major): D

## 委譲計画

- TASK-00010-01 docs-writer: README ロードマップ節 (v1.1.0 / v2.0.0 部分) を上記方針で書き換え。`v1.2.0` 区分を新設。利用者視点・トレース ID 非含有のポリシーを維持。

## スコープ外

- A〜F の設計・実装 (各バージョン着手時に別 task で起こす)
- `release-criteria.md` の ID 単位展開 (該当バージョン着手時に solution-architect が更新)
- `out-of-scope.md` の ID 移動 (該当 OOS-ID 該否は次バージョン設計時に判定)

## 進捗ログ

- 2026-04-20 project-master: ヒアリング完了 (A/B/C/F/D 採用)、docs-writer に委譲
- 2026-04-20 docs-writer: TASK-00010-01 完了 (README ロードマップ 5 区分へ再編、重複削除、将来検討温存)
- 2026-04-20 reviewer: TASK-00010-02 合格 (verify.sh 10/10 OK、README 以外無変更を git diff で確認)
- 2026-04-20 project-master: 親 task クローズ
