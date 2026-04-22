# TASK-00009-02 LICENSE (BSD-3-Clause / Taogya) 追加の最終確認

- Status: done
- Role: reviewer
- Parent: TASK-00009
- Related IDs: REQ-00001, NFR-00302

## 目的

docs-writer が TASK-00009-01 で行った LICENSE 同梱と関連メタ更新を最終確認し、v1.0.0 配布物として整合していることを確認する。

## 確認対象

- 新規 `LICENSE`
- 新規 `progress/docs-writer/TASK-00009-01-add-bsd3-license.md`
- 更新 `pyproject.toml`
- 更新 `README.md`
- 更新 `CHANGELOG.md`

## 確認結果

- LICENSE 本文: 合格。OSI 公式 BSD-3-Clause テンプレートと一致。1 行目 `BSD 3-Clause License`、`Copyright (c) 2026, Taogya`、3 条項 + 免責文を含む。全文 ASCII (非 ASCII 0 バイト)、末尾改行あり (1493 byte / 28 改行)。
- pyproject.toml: 合格。`[project]` に `license = "BSD-3-Clause"` (SPDX) と `license-files = ["LICENSE"]` を追加。PEP 639 準拠。version=1.0.0 維持。setuptools>=69 build-backend で `license-files` glob は LICENSE を解決可能。
- README.md: 合格。末尾に「## ライセンス」節を追加、利用者向けに 1 文で完結し LICENSE への相対リンクを持つ。トレース ID なしで README ポリシーと整合。
- CHANGELOG.md: 合格。v1.0.0 Added 末尾に LICENSE 同梱行を 1 行追記。Keep a Changelog 形式維持。
- 子 task ファイル (`progress/docs-writer/TASK-00009-01-add-bsd3-license.md`): 合格。status=done、進捗ログに変更ファイル列挙あり。

## 直接修正した範囲

- `progress/project-master/TASK-00009-license-bsd3.md` に必須フィールド `Role: project-master` / `Related IDs: REQ-00001, NFR-00302` を追記 (`scripts/verify.sh` の `check_progress_format.py` / `check_role_boundary.py` の FAIL 解消)。

## 検証

- `python -m pytest tests -q`: **119 passed in 0.24s** (回帰なし)。
  - 注: ルート直下の `python -m pytest` を素で実行すると `tmp/v0.1.0/tests/...` の旧スナップショットが収集され ImportError になるが、これは LICENSE 追加と無関係な既存事象 (`tmp/` は作業領域)。今回はスコープ `tests/` で実行。
- `MMDC_REQUIRED=0 bash scripts/verify.sh`: 上記の親 task ファイル修正後、**10/10 OK** (`check_id_format.py` / `check_id_uniqueness.py` / `check_id_references.py` / `check_doc_links.py` / `check_progress_format.py` / `check_mermaid_syntax.py` / `check_markdown_syntax.py` / `check_no_implementation_leak.py` / `check_role_boundary.py` / `check_oos_no_implementation.py`)。

## 差し戻し事項

- なし。

## 残課題 (本 task のスコープ外)

- v1.0.0 Git タグ付けはユーザー手動で実施 (TASK-00009 親 task に記載済み)。

## 進捗ログ

- 2026-04-20 reviewer: 起票。LICENSE / pyproject.toml / README.md / CHANGELOG.md / docs-writer 子 task をレビューし全合格。verify.sh の親 task FAIL を直接修正後、10/10 OK。pytest tests 119 passed。done。
