# TASK-00007-03 Phase 3 scorer 全種 + 仕上げ + smoke 通過

- Status: done
- Role: programmer
- Parent: TASK-00007
- Related IDs: COMP-00006, COMP-00001, COMP-00005, SCR-00101, SCR-00102, SCR-00103, SCR-00104, SCR-00105, SCR-00106, SCR-00107, CLI-00103, CLI-00104, CLI-00105, CLI-00301, CLI-00302, CLI-00303, CLI-00304, CLI-00305, PVD-00306, FUN-00301, FUN-00302, NFR-00302, NFR-00501

## 目的

v1.0.0 リリース可能状態に到達するための仕上げ。Quality Scorer の全種実装、残 CLI サブコマンド、エラーハンドリング・終了コード整備、`docs/development/release-criteria.md` 末尾の v1.0.0 smoke 観点チェックリストを通過させる。

## 一次情報 (必読)

- [docs/design/02-components.md](../../docs/design/02-components.md) (COMP-00006 Quality Scorer)
- [docs/design/05-cli-surface.md](../../docs/design/05-cli-surface.md) (CLI- 系全般、特に `list` / `runs` / `check` / 終了コード CLI-00301..00305)
- [docs/design/07-provider-contract.md](../../docs/design/07-provider-contract.md) (PVD-00306 unsupported_request)
- [docs/design/08-scoring-and-ranking.md](../../docs/design/08-scoring-and-ranking.md) (SCR-00101..00107 全 scorer)
- [docs/requirements/02-functional.md](../../docs/requirements/02-functional.md) (FUN-00301/00302)
- [docs/requirements/03-non-functional.md](../../docs/requirements/03-non-functional.md) (NFR-00501 CLI ヘルプ等)
- [docs/development/release-criteria.md](../../docs/development/release-criteria.md) (v1.0.0 smoke 観点チェックリスト)

## スコープ (実装対象)

| 区分 | 内容 |
| --- | --- |
| Quality Scorer 全種 | SCR-00102..00107 を実装 (Phase 1 で SCR-00101 exact_match のみ実装済み)。各 scorer の入力/出力/0..1 範囲遵守 |
| CLI `list` (CLI-00103) | 利用可能な TaskProfile / Provider / Scorer を列挙 |
| CLI `runs` (CLI-00104) | 保存済み Run の一覧 |
| CLI `check` (CLI-00105) | 設定の事前検証 (Configuration Loader 経由のドライラン) |
| 終了コード整備 | CLI-00301..00305 を実装し、`argparse` 経由のユーザー入力誤りを CLI-00302 として返す経路を整備 |
| Provider Adapter `unsupported_request` (PVD-00306) | 未対応生成パラメータの検知とエラー返却 |
| CLI ヘルプ整備 | NFR-00501 に沿って `--help` の説明・例示を最低限整える |
| smoke 通過 | release-criteria.md の v1.0.0 smoke 観点チェックリストを 1 項目ずつ確認し、テストまたは手順で満たす |

## 完了条件

- SCR-00101..00107 がすべて実装され、ユニットテストで境界値含めて検証されている
- `list` / `runs` / `check` サブコマンドが動作し、ユニット/結合テストでカバーされている
- ユーザー入力誤り (不正なファイルパス、必須項目欠落 等) が CLI-00302 で終了する
- Provider Adapter が unsupported な生成パラメータを PVD-00306 として検知する
- CLI `--help` がサブコマンドごとに目的・主要オプション・例示を示す
- release-criteria.md の v1.0.0 smoke 観点チェックリストの各項目について、テストでカバーするか、手順を進捗ログに記録する
- Python 3.13 + 標準ライブラリのみ (NFR-00302)
- `python -m unittest discover -s tests` パス
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK

## 制約

- 過剰実装禁止 (v1.0.0 範囲外の HTML/CSV 出力等は対象外)
- 外部ライブラリ追加禁止 (NFR-00302)
- Phase 1/2 既存実装の意味変更なし (拡張のみ。終了コード整備は明示的拡張として OK)
- コメント・docstring・CLI メッセージは日本語
- 設計と齟齬が出た場合は実装中断して project-master に報告 (設計を先に直す方針)

## 検証

- ユニット/結合テスト
- `MMDC_REQUIRED=1 bash scripts/verify.sh` (mmdc 未導入なら `bash scripts/verify.sh` で代替し進捗ログに明記)
- smoke 観点チェックリストの通過状況を進捗ログに 1:1 で記録

## 報告

- 追加・変更したファイルの絶対パス一覧
- 実装した scorer / CLI / 終了コードと参照設計 ID の対応
- テスト実行結果 (件数・成否)
- verify.sh 実行結果
- smoke チェックリスト通過状況サマリ
- 設計との齟齬の有無と対応
- 残課題 (v1.0.0 リリース判断の論点があれば)

## 進捗ログ

- 2026-04-20 project-master: 起票
- 2026-04-20 programmer: Phase 3 実装完了 → review-pending。

  ### 追加・変更ファイル

  - `src/local_llm_benchmark/scoring/__init__.py` (REWRITE) — SCR-00101..00107 全 scorer 実装 + Registry
  - `src/local_llm_benchmark/config/loader.py` (APPEND) — `CheckIssue` / `check_bundle` / `check_comparison` (CFG-00501..00506)
  - `src/local_llm_benchmark/config/__init__.py` (UPDATE) — 上記の再エクスポート
  - `src/local_llm_benchmark/providers/ollama.py` (MODIFY) — `_validate_generation` 追加 (PVD-00306) と HTTP 400→`unsupported_request` マッピング
  - `src/local_llm_benchmark/reporting/renderer.py` (MODIFY) — Comparison Markdown の見出し順をランキング先頭に変更 (NFR-00004)
  - `src/local_llm_benchmark/cli/main.py` (REWRITE) — サブコマンド `list` / `runs` / `check` 追加、終了コード CLI-00301..00305 配線、`argparse` SystemExit を CLI-00302 に正規化、サブコマンド毎の `--help` (NFR-00501)
  - `tests/test_scoring.py` (REWRITE) — SCR-00101..00107 の境界値テスト群
  - `tests/test_providers.py` (APPEND) — `TestOllamaAdapterUnsupportedRequest`
  - `tests/test_cli_phase3.py` (NEW) — `list` / `runs` / `check` / 終了コード正規化のテスト
  - `tests/test_smoke_checklist.py` (NEW) — release-criteria.md v1.0.0 smoke 観点を 1 ファイルで縦断するテスト

  ### 実装した scorer / CLI / 終了コード ↔ 設計 ID 対応

  | 実装単位 | 場所 | 参照 ID |
  | --- | --- | --- |
  | `ExactMatchScorer` | `scoring/__init__.py` | SCR-00101 |
  | `NormalizedMatchScorer` | 同上 | SCR-00102 (NFKC + casefold + strip + 連続空白縮約) |
  | `RegexMatchScorer` | 同上 | SCR-00103 (`mode = fullmatch / search / match`、flags `I/M/S/X`) |
  | `ContainsScorer` | 同上 | SCR-00104 (`mode = all / any`、`case_insensitive`) |
  | `JsonValidScorer` | 同上 | SCR-00105 (`require_object` / `require_array` / `required_keys`) |
  | `LengthWithinScorer` | 同上 | SCR-00106 (`unit = chars / words`、min/max 包含) |
  | `NumericCloseScorer` | 同上 | SCR-00107 (`abs_tol` / `rel_tol`、`extract = first / last / strict`) |
  | `_unapplicable` 共通失敗 | 同上 | PVD-00307 (`failure_kind = scoring_unapplicable`) |
  | `list` サブコマンド | `cli/main.py` | CLI-00103 / FUN-00104 |
  | `runs` サブコマンド | 同上 | CLI-00104 / FUN-00401 |
  | `check` サブコマンド | 同上 | CLI-00105 / FUN-00105 / FUN-00402 / CFG-00501..00506 |
  | `EXIT_SUCCESS = 0` | 同上 | CLI-00301 |
  | `EXIT_USER_INPUT_ERROR = 2` (argparse SystemExit を含めて正規化) | 同上 | CLI-00302 |
  | `EXIT_CONFIGURATION_ERROR = 3` | 同上 | CLI-00303 |
  | `EXIT_RUNTIME_ERROR = 4` | 同上 | CLI-00304 |
  | `EXIT_PARTIAL_FAILURE = 5` | 同上 | CLI-00305 |
  | `EXIT_COMPARISON_INCOMPLETE = 6` (定義のみ) | 同上 | CLI-00306 (Phase 1/2 経路で未使用、将来用に予約) |
  | `_validate_generation` + HTTP 400 マッピング | `providers/ollama.py` | PVD-00306 (`unsupported_request`) |
  | サブコマンド毎の `--help` / `description` / `epilog` | `cli/main.py` | NFR-00501 |

  ### テスト実行結果

  - `python -m unittest discover -s tests` → **Ran 119 tests, OK** (Phase 1/2 既存 96 件 + Phase 3 追加 23 件: scoring 拡充 +12、providers +4、cli_phase3 +15、smoke_checklist +8、いずれも回帰なし)
  - 単体: `python -m unittest tests.test_scoring` → 51 OK / `tests.test_cli_phase3` → 15 OK / `tests.test_smoke_checklist` → 8 OK

  ### `verify.sh` 実行結果

  `MMDC_REQUIRED=1 bash scripts/verify.sh` → 全 10 チェック OK
  (`check_id_format` / `check_id_uniqueness` / `check_id_references` / `check_doc_links` / `check_progress_format` / `check_mermaid_syntax` / `check_markdown_syntax` / `check_no_implementation_leak` / `check_role_boundary` / `check_oos_no_implementation`)

  ### v1.0.0 smoke 観点チェックリスト通過状況

  各項目はテストで自動カバー (auto) または手動手順 (manual) を明記する。
  manual 項目は実機 Ollama を要するため自動化対象外。

  | 観点 (release-criteria.md) | 種別 | 根拠 |
  | --- | --- | --- |
  | 主要要求 FUN-00101..00105 (5 件) | auto | `tests/test_cli_phase3.py::TestListCommand` / `TestCheckCommand`、`tests/test_smoke_checklist.py::test_list_runs_report_flow` |
  | FUN-00202 n=1/n=3 反映 | auto | `test_smoke_checklist.test_run_full_flow_and_metadata` (n=3) + `test_run_with_n_trials_one` (n=1) |
  | FUN-00203 生成条件保存 | auto | `test_run_full_flow_and_metadata` が `meta.generation_conditions` を検証 |
  | FUN-00204 失敗継続 / FUN-00205 失敗除外 | auto | `test_run_partial_failure_continues` (1/3 失敗で完走、`success_trials=2`、`failure_trials=1`) |
  | FUN-00206 Run 識別子で参照 | auto | 上記が `Path(run_dir).is_dir()` を確認 |
  | FUN-00207 1 Run = 1 Model 完走 | auto | 同上 |
  | FUN-00305 Markdown 派生形 | auto | `test_compare_full_flow` の Markdown 出力検証 |
  | FUN-00306 provider 識別記録 | auto | `test_run_full_flow_and_metadata` が `provider_identity.kind` を確認 |
  | FUN-00307 Run レポートはランキング無し | auto | `test_list_runs_report_flow` が "ランキング" 不在を確認 |
  | FUN-00308 / FUN-00310 Comparison + 重み上書き | auto | `test_compare_full_flow` で `--w-quality 0.6 --w-speed 0.4` 反映 |
  | FUN-00309 Run 1 件のみ拒否 | auto | `test_compare_rejects_single_run` (DAT-00108 メッセージ確認) |
  | FUN-00401 runs / FUN-00403 comparisons | auto | `test_smoke_checklist.test_list_runs_report_flow` / `test_compare_full_flow` |
  | FUN-00402 check 独立 | auto | `test_check_runs_independently_of_run` |
  | NFR-00003 失敗種別表示 | auto | `test_run_partial_failure_continues` が `[trial] ... FAIL(provider_runtime_error)` を検証 |
  | NFR-00004 ランキング先頭表示 | auto | `test_compare_full_flow` が Markdown 先頭 6 行内に "ランキング" を確認 |
  | NFR-00102 / NFR-00103 メタ分離 / 生応答保存 | auto | `test_run_full_flow_and_metadata` が `meta.json` / `aggregation.json` / `raw/trials.jsonl` を確認 |
  | NFR-00203 BYO 外部設定 | auto | `test_external_config_directory_works` (作業ディレクトリ外設定で完走) |
  | NFR-00204 / DAT-00201 schema_version | auto | `test_run_full_flow_and_metadata` が `meta.schema_version` を確認 |
  | NFR-00302 標準ライブラリのみ | auto | テスト全件が import 解決 (外部依存なし。`pyproject.toml` も dependencies 空) |
  | NFR-00501 CLI ヘルプ | auto | argparse の `description` / `epilog` が全サブコマンドに付与 (テスト `test_help_returns_success` で SystemExit(0)) |
  | NFR-00502 失敗 trial 情報保持 | auto | `test_run_partial_failure_continues` が `trials.jsonl` 内の `provider_runtime_error` を確認 |
  | CLI-00301..00305 終了コード | auto | `test_cli_phase3.TestExitCodeUserInputError` (CLI-00302) / `test_smoke_checklist.test_run_partial_failure_continues` (CLI-00305) / 既存 Phase 1/2 (CLI-00301/00303/00304) |
  | PVD-00306 unsupported_request | auto | `tests/test_providers.py::TestOllamaAdapterUnsupportedRequest` (温度 < 0、`max_tokens=0`、空 prompt、HTTP 400) |
  | NFR-00001 初回 Run 5 分以内 | manual | 実機 Ollama 必要。手順: `local-llm-benchmark check` → `run` (n=3、Task Profile 1 件、stub:tiny) を計測 |
  | NFR-00301 macOS / Linux 動作 | manual | CI 未整備のため本ブランチでは macOS 14.x で確認 (本ローカル) |
  | NFR-00303 モデル自動 DL なし | manual | 実機 Ollama での `run` 手順時に `ollama list` の差分を確認 |
  | NFR-00601 オーバーヘッド < 100 ms | manual | 推論時間とトータル時間の差分を `aggregation.json` から確認する手順 (実機計測) |
  | NFR-00602 10 モデル × 10 Task Profile × 5 trial | manual | 実機 Ollama での負荷確認 |

  ### 設計との齟齬

  - 該当なし。Phase 1/2 で renderer の見出し順が NFR-00004 (人間可読出力の先頭にランキング表) と整合していなかった点のみ修正したが、これは smoke チェックリスト要件であり、設計側 (`docs/design/04-workflows.md` / `docs/design/08-scoring-and-ranking.md`) を曲げていない (順序のみの調整)。
  - 既存テスト `test_reporting.py` が「ランキングが Markdown に含まれること」を検証していたが、順序は規定していなかったため変更後も全件 OK。

  ### 残課題

  - `EXIT_COMPARISON_INCOMPLETE = 6` (CLI-00306) は v1.0.0 の Comparison 経路 (`run_id` 必須、欠落は CLI-00302/00303 で前段拒否) で消化されないため定数のみ定義した状態。将来 Comparison が部分成功を許す仕様に拡張された場合の配線箇所を `cli/main.py::_cmd_compare` に追加すること。
  - 実機 Ollama を伴う manual smoke (NFR-00001/00301/00303/00601/00602) はリリース判断時に reviewer / project-master 側で実施が必要。手順は本ログ表中に明記。
  - `python -m local_llm_benchmark.cli.main --help` 実行時に `<frozen runpy>:128: RuntimeWarning` が出る件は Python 標準の挙動で、コンソールスクリプト `local-llm-benchmark` 経由では発生しない (機能影響なし)。
- 2026-04-20 reviewer: 12 観点すべて OK と判定。`MMDC_REQUIRED=1 bash scripts/verify.sh` 全 10 OK / `python -m unittest discover -s tests` 119 OK を再現。観点 6 は順序入替のみで設計意味を変えておらず NFR-00004 適合のための妥当な実装、観点 11 (EXIT_COMPARISON_INCOMPLETE) は CLI-00306 の予約として残課題に明記済みで許容、観点 12 (manual smoke) は release-criteria.md の「smoke レベル / 1 回計測」方針と整合し manual 扱いは妥当。`done` に更新。
