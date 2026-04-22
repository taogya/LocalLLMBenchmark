# TASK-00017 v2.0.0 Web UI 設計 (結果表示 + CLI 操作 UI 化)

- Status: open
- Role: project-master
- Related IDs: REQ-00001
- 起票日: 2026-04-22
- 対象バージョン: v2.0.0
- 区分: **設計のみ** (実装・テストは本 task では行わない)

## 目的

これまでユーザー主導で CLI から実施してきた一連の作業 (system-probe / config lint / model pull / warmup /
run / comparison) を、ブラウザから操作・参照できる Web UI として統合する。
v2.0.0 系の最後に位置する大物機能のため、本 task では **設計成果物の確定までを範囲** とし、実装と
テストは後続 task に分割する。

## 完了条件

- 以下が `docs/design/` 配下にまとまっている:
  - 画面構成 (ダッシュボード / Run 起動 / Provider 状態 / 結果一覧 / 比較表示)
  - 結果ストア (`./results`) を読み取り表示する範囲と形式
  - CLI 操作の UI 化対象一覧 (system-probe / config lint / model pull / warmup / run / compare 等)
  - 配布形式 (静的 HTML 生成 / ローカル HTTP サーバ / Electron 等) の比較と採用案
  - NFR-00302 (標準ライブラリ縛り) との整合方針 (例: 標準 `http.server` + 静的アセット)
  - 認証・公開範囲ポリシー (ローカル限定で十分か、外部公開を許すかの方針)
- `release-criteria.md` の v2.0.0 区分に Web UI の受入基準が ID 単位で展開される。
- 後続実装 task (UI 実装 / API 層実装 / 結果ビューア実装等) の分割案が親 task に列挙される。

## スコープ外

- UI 実装 / フロントエンド構築 / E2E テスト (本 task の後続で別 task 起票)
- 認証基盤 / 多人数同時利用 (個人ローカル運用が前提)
- Web UI からのファイル編集 (config 編集はテキストエディタを推奨)

## 想定委譲計画 (着手時に確定)

- solution-architect: 画面構成 / 配布形式 / NFR-00302 整合方針の確定
- reviewer: REQ-00001 (PC・用途への最適モデル選定支援) 中心目的との寄与度確認
- (実装着手後) programmer / docs-writer

## 進捗ログ

- 2026-04-22 project-master: v1.0.0 リリース後ヒアリング (Web UI 採用 / 設計タスクのみ起票方針) を踏まえ起票