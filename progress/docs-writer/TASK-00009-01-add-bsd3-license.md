# TASK-00009-01 LICENSE (BSD-3-Clause / Taogya) 同梱と関連メタ更新

- Status: done
- Role: docs-writer
- Parent: TASK-00009
- Related IDs: REQ-00001, NFR-00302

## 目的

v1.0.0 リリース直前に判明した LICENSE ファイル未同梱を解消する。著作権者 `Taogya` 名義で BSD-3-Clause を追加し、`pyproject.toml` (PEP 639) / `README.md` / `CHANGELOG.md` の利用者向け記述を整合させる。

## 完了条件

- リポジトリルートに `LICENSE` が存在し、本文が OSI 公式 BSD-3-Clause と一致する。
- 1 行目が `BSD 3-Clause License`、著作権表記が `Copyright (c) 2026, Taogya`。
- `pyproject.toml` の `[project]` に `license = "BSD-3-Clause"` と `license-files = ["LICENSE"]` が追加されている。
- `README.md` 末尾に「## ライセンス」節が存在し、BSD-3-Clause / Taogya / LICENSE 参照が日本語で短く書かれている。
- `CHANGELOG.md` v1.0.0 Added に LICENSE 同梱の 1 行が追記されている。

## スコープ外

- LICENSE 文面のレビュー (TASK-00009-02 で実施)
- v1.0.0 Git タグ付け (ユーザー手動)

## 進捗ログ

- 2026-04-20 docs-writer: 起票、LICENSE / pyproject.toml / README.md / CHANGELOG.md を更新。
- 2026-04-20 docs-writer: done。変更ファイル:
  - 新規 `LICENSE` (BSD-3-Clause, Copyright (c) 2026, Taogya / OSI 公式テンプレート本文)
  - 更新 `pyproject.toml` (`[project]` に PEP 639 形式で `license = "BSD-3-Clause"` と `license-files = ["LICENSE"]` を `description` 直後に追加)
  - 更新 `README.md` (末尾に「## ライセンス」節を追加。LICENSE への相対リンク)
  - 更新 `CHANGELOG.md` (v1.0.0 Added 末尾に LICENSE 同梱の 1 行を追記)
  - 新規 `progress/docs-writer/TASK-00009-01-add-bsd3-license.md` (本ファイル)
