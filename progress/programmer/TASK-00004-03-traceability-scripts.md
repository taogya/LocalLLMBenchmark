# TASK-00004-03 機械チェックスクリプト整備 (scripts/traceability + verify.sh)

- Status: review-pending
- Role: programmer
- Parent: TASK-00004
- Related IDs: TRC-00101..TRC-00104, PROG-00103, NFR-00302

## 目的

トレーサビリティとプロジェクト健全性の機械チェックを `scripts/traceability/` 配下に整備し、`scripts/verify.sh` で集約実行できるようにする。

## 成果物

### scripts/traceability/

| スクリプト | 検証内容 |
| --- | --- |
| `check_id_format.py` | 全 ID が `<Prefix>-NNNNN` (5 桁 0 埋め) を満たすか |
| `check_id_uniqueness.py` | カテゴリ内で ID が一意か / 欠番がないか (運用上欠番禁止) |
| `check_id_references.py` | 文書内で参照される ID が定義済みか (未定義参照の検出) |
| `check_doc_links.py` | Markdown リンクのターゲット存在検証 + 本文中のパス文字列 (拡張子 `.md|.py|.toml|.json|.yaml|.sh` 等) の存在検証 |
| `check_progress_format.py` | `progress/**/*.md` の `Status:` `Role:` `Parent:` `Related IDs:` 必須項目と状態遷移値 (`open|in-progress|review-pending|done|cancelled`) |
| `check_mermaid_syntax.py` | Mermaid 内の `<br/>` 等の確実な誤り検出 + 括弧/矢印 heuristic + `mmdc` がインストールされていれば実行 (なければ warn してスキップ) |
| `check_markdown_syntax.py` | コードフェンス・リンク括弧・表列数整合 |
| `check_no_implementation_leak.py` | 設計書 (`docs/requirements/`, `docs/design/`) に実装具体 (Python 関数名・クラス名・実装ライブラリ名) が混入していないか検出 |
| `check_role_boundary.py` | 各 progress task の `Role:` とファイル配置ディレクトリが一致するか |
| `check_oos_no_implementation.py` | (1) `src/` `tests/` `configs/` `prompts/` 内に `OOS-NNNNN` が出現していないか / (2) active な (非 cancelled/done) progress task の `Related IDs:` に OOS- が出現していないか |

### scripts/verify.sh

- 上記スクリプトを順次実行し、終了コードを集約
- 各スクリプトの終了コード: 違反 0 件 → 0 / 違反あり → 非 0
- 失敗時も他スクリプトの実行は継続し、最後に集約結果を表示

## 実装方針

- Python 標準ライブラリのみで実装 (NFR-00302)
- 各スクリプトは単独で実行可能 (`python scripts/traceability/check_xxx.py`)
- 共通ヘルパー (ID 抽出、ファイル走査) は `scripts/traceability/_common.py` に集約してよい
- Mermaid 検査の `mmdc` フォールスルーは Node.js 環境がない場合 warn のみで成功扱い (CI 強制しない)
- 出力形式: 各スクリプトとも `OK` または `[FAIL] <ファイル>:<行>: <理由>` を行単位で出力

## 既知違反の扱い

- 現リポジトリで違反が検出された場合、可能な限り修正する
- 修正不能 (設計判断が必要等) なものは task 本文に列挙し、project-master に差し戻し依頼

## 着手条件

- なし (TASK-00004-01 と並行可)
- ただし TASK-00004-01 完了後に再実行して違反 0 件を確認すること

## 完了条件

- 10 スクリプトと verify.sh が動作する
- 現状 (TASK-00004-01 完了後) で違反 0 件、もしくは既知許容項目のみ
- README または `scripts/traceability/README.md` で使い方を 1 ファイルにまとめる
- Status を `review-pending` に更新

## テスト

- 各スクリプトに対して、正常系と違反検出系の最小ケースを `tests/scripts/` に配置 (任意だが推奨)
- 違反検出は固定文字列 fixture でも可

## 進捗ログ

- 2026-04-19 programmer: 着手 (Status: in-progress)。TASK-00004-01 完了済みを確認。
- 2026-04-19 programmer: 実装完了 (Status: review-pending)。
  - 実装ファイル
    - [scripts/traceability/_common.py](../../scripts/traceability/_common.py)
    - [scripts/traceability/check_id_format.py](../../scripts/traceability/check_id_format.py)
    - [scripts/traceability/check_id_uniqueness.py](../../scripts/traceability/check_id_uniqueness.py)
    - [scripts/traceability/check_id_references.py](../../scripts/traceability/check_id_references.py)
    - [scripts/traceability/check_doc_links.py](../../scripts/traceability/check_doc_links.py)
    - [scripts/traceability/check_progress_format.py](../../scripts/traceability/check_progress_format.py)
    - [scripts/traceability/check_mermaid_syntax.py](../../scripts/traceability/check_mermaid_syntax.py)
    - [scripts/traceability/check_markdown_syntax.py](../../scripts/traceability/check_markdown_syntax.py)
    - [scripts/traceability/check_no_implementation_leak.py](../../scripts/traceability/check_no_implementation_leak.py)
    - [scripts/traceability/check_role_boundary.py](../../scripts/traceability/check_role_boundary.py)
    - [scripts/traceability/check_oos_no_implementation.py](../../scripts/traceability/check_oos_no_implementation.py)
    - [scripts/verify.sh](../../scripts/verify.sh)
    - [scripts/traceability/README.md](../../scripts/traceability/README.md)
  - `bash scripts/verify.sh` 結果
    - 9 スクリプト OK / 1 スクリプト FAIL (`check_oos_no_implementation.py`, 持ち越し 3 件)
  - 修正した違反
    - 自身が新規作成したファイルのみ。docs/ の既存内容は機械的書き換えを行わず。
  - 持ち越し違反 (project-master へ差し戻し依頼)
    - active task の `Related IDs:` に `OOS-` が含まれる:
      - `progress/project-master/TASK-00001-design-bootstrap.md:5`
      - `progress/project-master/TASK-00004-run-model-pivot.md:5`
      - `progress/solution-architect/TASK-00004-01-design-rewrite.md:6`
    - これらは他ロール所有の task のため、programmer 単独で書き換えない。
      project-master 経由で各 task を `done` 化するか、`Related IDs:` から `OOS-` を除外する判断が必要。
  - 設計判断ヒューリスティック (本文に明記)
    - **ID 定義の判定**: prefix ごとの「正本ドキュメント」 (`_common.CANONICAL_DEF_DOCS`)
      内の表行先頭セル / 見出し行のみを定義として扱う。同一ファイル内の表 + 見出し
      による重複は許容し、ファイル間重複のみエラー。
    - **欠番判定**: 同一 prefix の subgroup (百の位) 単位で連続性を検査。
      実際の採番運用 (FUN-001xx 登録系 / FUN-002xx Run 系...) に合わせた緩めの方針。
    - **Mermaid `<br/>` 検出**: 自己終了タグ (`<br/>`) のみ。
      Mermaid 公式ラベル改行 (`<br>`) は許容。
    - **implementation-leak**: 散文中のメタ言及 (例:「argparse / click 等」) は許容し、
      コードフェンス内・インラインコード内のみ検査対象。
  - 残課題 / リスク
    - `mmdc` (Mermaid CLI) を CI に入れていないため、構文の最終検証は warn 扱い。
      Node.js 環境が許容できれば `mmdc` 導入で完全検証に拡張可能。
    - リンクの anchor (`#section`) 妥当性検査は未対応。
    - テストコードは未実装 (任意指定のため割愛。本体スクリプトの自己検査
      = `bash scripts/verify.sh` で代替)。
