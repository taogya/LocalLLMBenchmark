# scripts/traceability

トレーサビリティとプロジェクト健全性の機械チェック群です (TASK-00004-03)。

- 全スクリプトは Python 3.13 標準ライブラリのみで動作 (NFR-00302)
- 各スクリプトは単独実行可能
  - `python scripts/traceability/check_xxx.py`
- 出力形式: `OK` または `[FAIL] <ファイル>:<行>: <理由>` (行単位)
- 終了コード: 違反 0 件 → 0 / 違反あり → 1

## 一括実行

```sh
bash scripts/verify.sh
```

各 check スクリプトを順次実行し、最後に集約結果を表示します。1 件でも失敗があれば exit 1 で終了します。

## スクリプト一覧

| スクリプト | 検証内容 |
| --- | --- |
| `_common.py` | 共通ヘルパー (ID 抽出、ファイル走査、出力フォーマット) |
| `check_id_format.py` | 全 ID が `<Prefix>-NNNNN` (5 桁 0 埋め) を満たすか |
| `check_id_uniqueness.py` | カテゴリ内で ID 定義が一意か / subgroup (百の位) 内で欠番が無いか |
| `check_id_references.py` | 参照される ID が定義済みか (`docs/{requirements,design,development}/` 出現を定義として扱う。TASK- は `progress/` 由来) |
| `check_doc_links.py` | Markdown リンク `[text](path)` と裸のパス文字列 (`.md|.py|.toml|.json|.yaml|.yml|.sh`) の存在検証 |
| `check_progress_format.py` | `progress/**/*.md` の必須フィールド・状態値・ファイル名形式 |
| `check_mermaid_syntax.py` | Mermaid `<br/>` 検出 + 括弧ヒューリスティック + (任意) `mmdc` 実行 |
| `check_markdown_syntax.py` | コードフェンス・リンク括弧・表列数の整合 |
| `check_no_implementation_leak.py` | `docs/requirements/` `docs/design/` の **コードフェンス内** または **インラインコード内** に実装具体 (argparse, click, ...) が混入していないか |
| `check_role_boundary.py` | `progress/<role>/` ディレクトリと task の `Role:` 値が一致するか |
| `check_oos_no_implementation.py` | (1) `src/`/`tests/`/`configs/`/`prompts/` 内に `OOS-` が無いか / (2) active な (非 cancelled/done) progress task の `Related IDs:` に `OOS-` が無いか |

## 実装メモ

### ID 定義 / 参照 の判定

- 「定義」: テーブル行 `| ID-00001 | ... |` の先頭セル、または見出し行 `## ID-00001 ...` の出現。
- 「参照」: それ以外の出現すべて (本文中の括弧内、リスト項目内など)。
- supersede 運用 (`(superseded by NEW-ID)`) は旧 ID を「定義済み」扱いのまま残す方針 (`docs/development/traceability.md` TRC-00002, TRC-00003)。

### 欠番判定の subgroup

ID の番号は同一カテゴリで「百の位」ごとに subgroup を形成する場合がある (例: FUN-001xx は登録系, FUN-002xx は Run 系)。`check_id_uniqueness.py` の欠番チェックは **subgroup 内** での連続性のみを検査する。

### Mermaid CLI

`mmdc` (Mermaid CLI) があれば構文を実際にレンダリング検証する。無ければ `[WARN]` を出して CLI 検証はスキップする (CI を Node.js 環境に依存させない)。環境変数 `MMDC` で実行ファイルパスを上書きできる。

環境変数 `MMDC_REQUIRED=1` をセットした場合、`mmdc` 不在を `[WARN]` ではなく FAIL として扱う (TASK-00005-01)。CI / ローカル検証で mmdc レンダリングを必須化したいときに使う。

```sh
MMDC_REQUIRED=1 bash scripts/verify.sh
```

`mmdc` の puppeteer が要求する Chrome 版が無い場合は次でインストールする:

```sh
npx puppeteer browsers install chrome-headless-shell@<version>
```

### implementation leak の判定範囲

`check_no_implementation_leak.py` は **コードフェンスとインラインコード内** に限り検査する。散文中で「argparse / click 等」と書く形のメタ言及は許容する。例外語は `_common.py` の `IMPL_LEAK_WHITELIST_TERMS` で管理する。

## 既知の限界

- リンク先存在検証は相対パスのみ。anchor (`#section`) の妥当性は検査しない。
- Markdown 構文検査は最低限のヒューリスティックで、CommonMark 完全準拠の構文判定は行わない。
- ID 欠番判定の subgroup 単位は採番運用 (`docs/development/traceability.md`) を前提とした実用ヒューリスティックである。
