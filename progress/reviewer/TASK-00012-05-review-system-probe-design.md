# TASK-00012-05 system-probe 設計確定レビュー

- Status: done
- Role: reviewer
- Parent: TASK-00012
- Related IDs: REQ-00001, FUN-00404, FUN-00405, CLI-00109, PROG-00103
- 起票日: 2026-04-23

## 目的

TASK-00012-01 の設計変更を確認し、`system-probe` の仕様が実装着手条件を満たすかを判定する。あわせて、TASK-00012 で触れた docs/design の追記に未確定情報が混入していないかを確認する。

## 完了条件

- TASK-00012-01 の成果が `system-probe` 実装に十分な粒度で確定している。
- `check` / `system-probe` / 将来の `config lint` / `config dry-run` の責務境界が矛盾なく整理されている。
- docs/design の TASK-00012 起因の追記に、名称や責務が未確定な将来情報を既定仕様として書いていない。
- 差し戻し事項があれば、対象ファイルと論点を明記している。

## スコープ外

- `system-probe` 実装そのもの
- README 更新
- docs/design 全体の運用監査 (TASK-00018 で対応)

## 進捗ログ

- 2026-04-23 project-master: 起票。TASK-00012-01 は review-pending だが、programmer 着手前に reviewer の設計確認を挟む必要があるため追加
- 2026-04-23 reviewer: TASK-00012-01 と関連 docs/requirements, docs/design, docs/development を確認。`check` の現行実装が静的検証のみであること、`system-probe` の入力・出力・終了状態・provider probe 契約が programmer 着手に足る粒度で確定していることを確認した。未確定情報として将来の `config lint` / `config dry-run` 名称が docs/design に残るが、これは TASK-00012 実装ブロッカーではなく TASK-00018 側で扱う一般論として整理した。`MMDC_REQUIRED=1 bash scripts/verify.sh` は 10/10 OK。

## レビュー記録 (reviewer 用)

### 判定

- 合格

### verify.sh 実行結果サマリ

- OK: check_id_format.py
- OK: check_id_uniqueness.py
- OK: check_id_references.py
- OK: check_doc_links.py
- OK: check_progress_format.py
- OK: check_mermaid_syntax.py
- OK: check_markdown_syntax.py
- OK: check_no_implementation_leak.py
- OK: check_role_boundary.py
- OK: check_oos_no_implementation.py

### 確認対象

- progress/solution-architect/TASK-00012-01-design-system-probe.md
- docs/requirements/02-functional.md
- docs/design/02-components.md
- docs/design/04-workflows.md
- docs/design/05-cli-surface.md
- docs/design/06-configuration-sources.md
- docs/design/07-provider-contract.md
- docs/development/release-criteria.md
- src/local_llm_benchmark/cli/main.py (`_cmd_check` の現行責務確認)

### 発見事項

- 観点 1: 合格。`system-probe` について、入力を CFG-00102 / CFG-00104 に限定する点、JSON 一次 / Markdown 派生の 4 セクション出力、host facts の best-effort、provider 到達確認と model ref 解決の責務、CLI-00307 の扱いが設計 task と docs/design 上で整合している。programmer は docs/design/04〜07 と docs/requirements/02 を正本として実装着手可能。
- 観点 2: 合格。現行 `src/local_llm_benchmark/cli/main.py` の `_cmd_check` は `load_config_bundle` / `check_bundle` / `check_comparison` の静的検証のみで、provider 通信や host hardware 収集を行っていない。これと docs/design/05-cli-surface.md, docs/design/06-configuration-sources.md, docs/design/07-provider-contract.md の責務境界記述は矛盾していない。
- 観点 3: 条件付き合格。TASK-00012 起因の docs/design 追記には、将来の `config lint` / `config dry-run` への言及が残る。例: docs/design/04-workflows.md, docs/design/05-cli-surface.md, docs/design/06-configuration-sources.md, docs/design/07-provider-contract.md。いずれも現行 `system-probe` の既定仕様を壊すものではなく、未確定名を「将来の面」として境界説明に使っている段階に留まる。
- 観点 4: 未確定情報の切り分け。`config lint` を新 public surface にするか `check` の互換 alias として扱うかという名称整理は TASK-00012 の blocker ではない。`system-probe` 実装に必要なのは「静的検証は `check` 側、動的観測は `system-probe` 側」という責務境界であり、これは確定済み。未確定な将来名称の docs/design での扱いは TASK-00018 側の一般論として整理するのが妥当。
- 観点 5: 合格。対象 progress / markdown に対して get_errors を実行し、明らかな問題は検出されなかった。

### 直接修正した範囲

- なし (review 記録のみ更新)

### 差し戻し事項

- なし

### ユーザー報告可否

- 可。TASK-00012 はこのまま programmer の実装着手へ進めてよい。

### 残課題メモ

- docs/design における将来 public surface の表現整理 (`config lint` / `config dry-run` の書き方) は TASK-00018 側で扱うのが妥当。
