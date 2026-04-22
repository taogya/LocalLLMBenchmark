# TASK-00009 LICENSE 追加 (BSD-3-Clause / Taogya)

- Status: done
- Role: project-master
- Related IDs: REQ-00001, NFR-00302
- 起票日: 2026-04-20
- 完了日: 2026-04-20

## 目的

v1.0.0 リリース直前にライセンスファイルが未同梱であることが判明したため、
著作権者 `Taogya` 名義で BSD-3-Clause ライセンスを追加し、配布物として完結させる。

## 委譲計画

- TASK-00009-01 docs-writer:
  - リポジトリルートに `LICENSE` を BSD-3-Clause / Copyright (c) 2026 Taogya で新規作成
  - `pyproject.toml` の `[project]` に `license = "BSD-3-Clause"` と `license-files = ["LICENSE"]` (PEP 639) を追加
  - `README.md` 末尾に「ライセンス」節を追加 (BSD-3-Clause / LICENSE 参照)
  - `CHANGELOG.md` の v1.0.0 Added に LICENSE 同梱を追記
- TASK-00009-02 reviewer:
  - LICENSE 文面が OSI 公式テキストと一致するか確認
  - pyproject.toml の license 表記が PEP 639 に準拠するか確認
  - README/CHANGELOG/pyproject の整合性確認

## 残課題 (本 task のスコープ外)

- v1.0.0 Git タグ付け (ユーザー手動) は本対応反映後に実施

## 進捗ログ

- 2026-04-20 project-master: 親 task 起票、docs-writer に委譲
- 2026-04-20 docs-writer: TASK-00009-01 完了 (LICENSE 新規 / pyproject.toml に PEP 639 license 追加 / README にライセンス節 / CHANGELOG 追記)
- 2026-04-20 reviewer: TASK-00009-02 合格 (LICENSE 本文 OSI 一致、PEP 639 準拠、119 tests OK、verify.sh 10/10 OK)
- 2026-04-20 project-master: 親 task クローズ
