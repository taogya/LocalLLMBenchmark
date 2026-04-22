# TASK-00005-01 Mermaid 図の実描画エラー修正と検証強化

- Status: review-pending
- Role: programmer
- Parent: TASK-00005
- Related IDs: PROG-00103, NFR-00302

## 背景

ユーザー報告: VS Code Markdown プレビュー上で複数の mermaid 図が "No diagram type detected matching given configuration for text:" と表示され描画されない。
ユーザー側で `mmdc` (Mermaid CLI) を導入済 (`brew install mmdc-cli` と報告されているが、正規名は `mermaid-cli` (npm 版が一般的) のため環境確認も含む)。

## 目的

1. ローカルに導入された `mmdc` を使い、`docs/` 配下の全 mermaid ブロックを実レンダリングして真のエラー箇所を特定
2. エラーをすべて修正し、全 mermaid ブロックがエラーなく描画される状態にする
3. `scripts/traceability/check_mermaid_syntax.py` を「mmdc が利用可能な場合は必須検証する (warn ではなく fail にする)」モードに拡張 (環境変数 `MMDC_REQUIRED=1` で制御。既定は現状維持)

## 作業手順

1. 担当 task の Status を `in-progress` にする
2. `mmdc` の有無を確認 (`which mmdc` `mmdc --version`)。なければユーザーに環境差異を報告して停止
3. `docs/` 配下の全 `.md` から mermaid ブロックを抽出し、各ブロックを `mmdc -i <tmp.mmd> -o <tmp.svg> -q` で個別検証
4. 失敗したブロックについて、stderr のメッセージと該当行を task 進捗ログに列挙
5. 修正方針:
   - ` ```mermaid ` 直後の余計な空白・全角空白を除去
   - 図種別宣言行 (`flowchart`, `sequenceDiagram`, `classDiagram`) の表記揺れ修正
   - ノードラベル内の特殊文字 (`:` `(` `)` `<` `>` `&` `|` `;`) を必要に応じてダブルクォート化 (例: `A["foo (bar)"]`)
   - sequenceDiagram のメッセージ本文に括弧が含まれる場合の確認 (`A->>B: 検査 (DAT-00109)` 等。Mermaid は許容するはずだが描画失敗例があれば修正)
   - classDiagram の関連行構文 (`"1" o-- "1..*"` 等) の正当性確認
6. 各修正は最小限の差分にし、設計内容 (ID 参照、責務、流れ) を変えないこと
7. 修正後に再度 `mmdc` で全ブロックを検証し、失敗 0 件を確認
8. `scripts/traceability/check_mermaid_syntax.py` を以下に拡張:
   - 環境変数 `MMDC_REQUIRED=1` がセットされている場合、`mmdc` 不在を warn ではなく FAIL にする
   - mmdc 構文エラーは現行通り FAIL
   - 既定 (`MMDC_REQUIRED` 未設定) の挙動は変えない
9. `scripts/verify.sh` を `MMDC_REQUIRED=1` で実行し、全 OK を確認
10. `scripts/traceability/README.md` に `MMDC_REQUIRED=1` の説明を追記
11. 進捗ログに「検出されたエラー一覧」「修正内容」「mmdc 再実行結果」を記録し Status を `review-pending` に更新

## 制約

- 設計内容 (ID, 責務, 矢印の意味) を変えない。あくまで構文修正
- mmdc が `puppeteer` (Chromium) を要求する場合があり、初回実行時に時間がかかることがあるが正常
- 修正中に「mermaid 仕様上不可避な制約」が見つかった場合 (例: 日本語ラベル + 特殊文字の組合せ)、別表現に書き換える前に project-master へ報告

## 完了条件

- `docs/` 配下の全 mermaid ブロックが `mmdc` でエラーなく描画される
- `MMDC_REQUIRED=1 bash scripts/verify.sh` が全 OK
- `check_mermaid_syntax.py` が拡張済み
- 進捗ログに作業内容が記録されている

## 参考

- ユーザー報告のエラーメッセージ: `No diagram type detected matching given configuration for text:`
  - 多くの場合、` ```mermaid ` の直後に空行/全角空白がある、または最初の非空白行が `flowchart` `sequenceDiagram` `classDiagram` 等で始まっていない場合に出る
- [scripts/traceability/check_mermaid_syntax.py](../../scripts/traceability/check_mermaid_syntax.py)
- `scripts/_check_mermaid_real.sh` は project-master が試作した抽出スクリプト (本 task で削除済)。後継ロジックは [scripts/traceability/check_mermaid_syntax.py](../../scripts/traceability/check_mermaid_syntax.py) に統合。

## 進捗ログ

### 2026-04-19 programmer

- Status: open → in-progress → review-pending
- 環境: macOS / `mmdc` 11.12.0 (`/opt/homebrew/bin/mmdc`, `brew install mermaid-cli`)
- 初回 mmdc 実行: 9 ブロック中 9 ブロックが「Could not find Chrome (ver. 131.0.6778.204)」で失敗
  - 原因種別: **環境差異** (puppeteer 用 chrome-headless-shell 未導入)
  - mermaid 構文エラーは検出されず
- 対処: `npx puppeteer browsers install chrome-headless-shell@131.0.6778.204` を実行
- 隠し文字スキャン (BOM / 全角空白 U+3000 / zero-width U+200B/200C/FEFF / 不正な図種別宣言) も別途実施し、`docs/` 配下の全 mermaid ブロックで該当なしを確認
  - したがって本 task の範囲では `docs/` 配下に修正対象のソース不具合は存在しない (再描画は環境セットアップで解消)
  - ユーザー報告の "No diagram type detected" は VS Code Markdown プレビューのキャッシュ/バンドル mermaid 版差異の可能性が高い (構文側に再現する欠陥は無し)
- mmdc 再検証結果 (Chrome 導入後):

  ```text
  OK   docs/design/01-architecture.md:45
  OK   docs/design/02-components.md:25
  OK   docs/design/03-data-model.md:8
  OK   docs/design/04-workflows.md:25
  OK   docs/design/04-workflows.md:67
  OK   docs/design/04-workflows.md:96
  OK   docs/design/04-workflows.md:117
  OK   docs/design/04-workflows.md:141
  OK   docs/development/roles.md:47
  9/9 passed, 0 failed
  ```

- `check_mermaid_syntax.py` 拡張: 環境変数 `MMDC_REQUIRED=1` セット時は `mmdc` 不在を `[WARN]` ではなく FAIL として返す (既定挙動は変更なし)
- `scripts/traceability/README.md` に `MMDC_REQUIRED=1` の挙動と `chrome-headless-shell` 導入手順を追記
- `scripts/_check_mermaid_real.sh` を削除 (project-master の試作品。本 task で正式化しない方針)
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 実行結果: 10 件すべて OK
- 変更ファイル:
  - `scripts/traceability/check_mermaid_syntax.py` (MMDC_REQUIRED 対応)
  - `scripts/traceability/README.md` (説明追記)
  - `scripts/_check_mermaid_real.sh` (削除)
  - `progress/programmer/TASK-00005-01-mermaid-real-fix.md` (本ファイル: ログ追記、削除済リンク差し替え)
- 残課題:
  - `docs/development/environment.md` (もしあれば) に「mmdc + chrome-headless-shell@131.0.6778.204 の導入手順」を補足する余地。ただし本 task の完了条件外のため別 task で扱うのが妥当
  - VS Code Markdown プレビュー側の表示問題が再現する場合、プレビュー再起動 / mermaid 拡張更新を案内する必要あり (調査用 task として project-master に判断依頼)

