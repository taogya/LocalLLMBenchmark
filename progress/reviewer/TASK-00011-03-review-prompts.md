# TASK-00011-03 prompt 仕様・文面・整合確認

- Status: done
- Role: reviewer
- Parent: TASK-00011
- Related IDs: REQ-00001
- 起票日: 2026-04-22

## 目的

TASK-00011-01 と TASK-00011-02 の成果物を確認し、`.github/prompts/` の prompt 群が
利用者視点・中心目的・既存 config サンプルとの整合を満たしていることを検証する。

## 完了条件

- `.github/prompts/` 配下の prompt が task の完了条件を満たす
- 利用者視点であり、トレース ID や内部設計寄りの不要情報を含まない
- コンフィグ生成 prompt の出力が sample config を誤上書きしない導線になっている
- model-recommender prompt の情報源方針が一次情報優先ルールに反していない
- 診断レポート prompt の有無が TASK-00011-01 の結論と一致している

## スコープ外

- prompt 本体の新規執筆
- v1.2.0 以降の CLI / Web UI 機能

## 確認結果

- 観点 1 (`.github/prompts/` 配下に 2 prompt のみ、診断レポート prompt なし): OK
	- `.github/prompts/` 配下は `config-generator.prompt.md` と `model-recommender.prompt.md` の 2 件のみで、TASK-00011-01 の結論どおり診断レポート prompt は追加されていない。
- 観点 2 (`config-generator.prompt.md`): OK
	- 1 回で 1 ファイルだけ生成する前提、出力先フォルダ確認、`configs/` を read-only sample とする扱い、sample 上書き禁止、TaskProfile / Provider / Run / Comparison ごとの必須ヒアリングと最小 TOML 項目、`model_candidates.toml` 生成対象外を再確認した。
	- 前回レビューで解消した doc link 誤検出回避の prose 表現も維持されている。
- 観点 3 (`model-recommender.prompt.md`): OK
	- provider を最初に聞くこと、公式情報優先・不足時のみ補助情報・Web 不可時フォールバック、PC スペック / 用途 / 制約に基づく候補比較と推奨理由の返答形式、現行 repo で benchmark 実行整合がある provider は Ollama のみである注記を再確認した。
- 観点 4 (利用者視点・トレース ID 非含有): OK
	- 2 prompt とも利用者向けの文面であり、トレース ID や内部設計寄りの識別子は含まない。
- 観点 5 (子 task の status / 進捗ログ): OK
	- 親 / 設計 / 執筆 task の状態と本文の整合を確認し、本 task に再レビュー結果を追記した。
- 観点 6 (`get_errors`): OK
	- 対象 prompt 2 件と task 4 件にエラーは無いことを確認した。

## verify.sh 実行サマリ (`MMDC_REQUIRED=1`)

- OK `check_id_format.py`
- OK `check_id_uniqueness.py`
- OK `check_id_references.py`
- OK `check_doc_links.py`
- OK `check_progress_format.py`
- OK `check_mermaid_syntax.py`
- OK `check_markdown_syntax.py`
- OK `check_no_implementation_leak.py`
- OK `check_role_boundary.py`
- OK `check_oos_no_implementation.py`

## 直接修正した範囲

- `.github/prompts/config-generator.prompt.md`
	- 出力先の既定形 3 箇所を裸パス誤検出しない prose 表現へ修正し、`python scripts/traceability/check_doc_links.py` の OK を確認した。
- `progress/reviewer/TASK-00011-03-review-prompts.md`
	- 前回レビュー記録に残っていた旧失敗内容を現行状態へ更新し、未定義 ID の stale 参照を除去した。

## 差し戻し事項

- なし。

## 総合判定

- prompt 本文の確認観点は合格。
- project-master 側で前回差し戻しとなった命名規約違反と ID 参照不整合は解消済みで、再レビュー時点の `MMDC_REQUIRED=1 bash scripts/verify.sh` も全 OK と確認した。
- 本 task の Status は `done` とする。

## 進捗ログ

- 2026-04-22 project-master: 子 task 起票。仕様確定と prompt 執筆の完了待ち
- 2026-04-22 reviewer: Status を `in-progress` 相当で着手。parent / design / docs-writer task と prompt 2 件を確認し、観点 1〜6 のうち prompt 内容はすべて OK と判定した。
- 2026-04-22 reviewer: `MMDC_REQUIRED=1 bash scripts/verify.sh` を実行。`check_doc_links.py` の失敗を `.github/prompts/config-generator.prompt.md` の軽微修正で解消し、単体再実行で OK を確認した。
- 2026-04-22 reviewer: full verify を再実行し、当時の残存 fail は project-master 側の未定義 ID 参照と親 task を含むファイル名規約違反であることを確認。差し戻し事項を記録し、本 task を `review-pending` に更新した。
- 2026-04-22 reviewer: project-master 側の命名規約違反と ID 参照不整合の修正後に再レビューを実施。観点 1〜6 の退行なし、対象ファイルのエラーなし、`MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 OK を確認し、本 task を `done` に更新した。