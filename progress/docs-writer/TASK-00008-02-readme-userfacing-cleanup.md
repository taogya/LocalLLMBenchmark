# TASK-00008-02 README からトレース ID 除去 + store-root パス見直し

- Status: done
- Role: docs-writer
- Parent: TASK-00008
- Related IDs: REQ-00001

## 目的

ユーザー指摘 (2026-04-20) に基づき、利用者向けドキュメント (README.md, configs/README.md) を「ユーザーが読みやすい状態」に整える。

## 指摘内容

1. **トレース ID の混入**: `REQ-` / `NFR-` / `FUN-` / `CLI-` / `SCR-` / `COMP-` / `DAT-` / `PVD-` / `CFG-` / `ARCH-` / `OOS-` / `ROLE-` / `TASK-` 等のトレース ID は内部運用上のものであり、利用者向けドキュメントには出さない。
2. **`--store-root tmp/results` の不適切さ**: `tmp/` は本リポジトリの作業領域 (gitignore 済) で、利用者が任意で使う領域ではない。利用者向け手順としては:
   - 利用者の作業ディレクトリに作る前提で `./results` 等の素直なパスを使う
   - 事前に `mkdir -p` する手順を入れるか、または store-root を引数で渡すこと自体の必要性を見直す

## 成果物

### 1. README.md (修正)

- トレース ID 列をすべて除去 (機能説明の自然な日本語に置き換え)
- 「サブコマンド一覧」表からも ID 列を削除し、コマンド名と用途の 2 列にする
- 「最短手順」のサンプルコマンドを以下のいずれかに修正:
  - 案 A (推奨): `--store-root ./results` に変更し、手順 0 として `mkdir -p ./results` を追加
  - 案 B: `--store-root` のデフォルトが定義されているなら省略してデフォルトを使う形に変更
  - docs-writer 判断で適切な方を選択 (実装の挙動を `src/local_llm_benchmark/cli/main.py` で確認し、デフォルトがあるなら案 B、無いなら案 A)
- 「関連ドキュメント」「ロードマップ」等の既存セクションでもトレース ID を除去
- リンク先 (docs/design/ 等) は残してよいが、本文中の ID 引用は削除

### 2. configs/README.md (修正)

- 同じく `CFG-` / `TASK-` / `REQ-` 等のトレース ID をすべて除去
- ファイルの説明は「Task Profile を定義する」「Ollama Provider 設定」等の自然な日本語に置き換え

### 3. CHANGELOG.md (確認のみ)

- CHANGELOG はリリースノートとして開発由来 ID を含めても問題ない (利用者は CHANGELOG を見るが、変更内容の追跡 ID は許容範囲)
- ただし読みづらくなる箇所があれば軽く整理してよい

## 完了条件

- README.md / configs/README.md からトレース ID 引用が消えている
  - 確認: `grep -E "(REQ|NFR|FUN|CLI|SCR|COMP|DAT|PVD|CFG|ARCH|OOS|ROLE|TASK|FLW)-[0-9]" README.md configs/README.md` が 0 件
- store-root の手順が「ユーザーが何もせず実行できる」状態になっている
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK
- 既存のセクション構成は可能な限り温存

## 制約

- 実装ファイル (`src/`) には触らない
- 設計書 (`docs/design/`, `docs/requirements/`) には触らない
- 中心目的 (REQ-00001 = ユーザーの PC・用途で最適なローカルモデルを選ぶ) からズレた追記をしない
- 言語: 日本語 (固有名詞は英語のまま)

## 報告

- 変更したファイルの絶対パス一覧
- README から除去した ID 件数 (概算)
- store-root の対応方針 (案 A / 案 B / その他)
- verify.sh 実行結果
- 残課題

## 進捗ログ

- 2026-04-20 project-master: 起票
- 2026-04-20 docs-writer: README.md / configs/README.md からトレース ID を除去。`--store-root` は ResultStore が自動生成するため `./results` を渡すだけで動く旨を明記し、サンプルコマンドを `tmp/results` → `./results` に変更。CHANGELOG.md は許容範囲のため未変更。verify.sh はこのモードで terminal 実行手段がないため未実行 (要レビュー時実行)。Status を `review-pending` に更新。
- 2026-04-20 reviewer: `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 OK。`grep -E "(REQ|NFR|FUN|CLI|SCR|COMP|DAT|PVD|CFG|ARCH|OOS|ROLE|TASK|FLW)-[0-9]" README.md configs/README.md` 0 件確認。store-root の自動生成挙動 (`src/local_llm_benchmark/storage/__init__.py:103` `self.root.mkdir(parents=True, exist_ok=True)`) と README 記述の一致を確認。サブコマンド表 7 件 (check/list/run/runs/compare/comparisons/report) は CLI 実装 (`src/local_llm_benchmark/cli/main.py` の `add_parser` 7 箇所) と一致し誤誘導なし。設計書 (docs/design/, docs/requirements/) は未変更。done に確定。
