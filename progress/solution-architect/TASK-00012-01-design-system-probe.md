# TASK-00012-01 system-probe 仕様と関連設計確定

- Status: done
- Role: solution-architect
- Parent: TASK-00012
- Related IDs: REQ-00001, FUN-00404, FUN-00405, FUN-00402, NFR-00301, NFR-00302, CLI-00105, CLI-00109, CLI-00307, CFG-00102, CFG-00104, CFG-00601, CFG-00602, CFG-00603, PVD-00004, PVD-00106, PVD-00107, PVD-00209, PVD-00210, PVD-00211, PVD-00406, FLW-00003, FLW-00007
- 起票日: 2026-04-22

## 目的

TASK-00012 で追加する `system-probe` サブコマンドについて、出力スキーマ、収集対象、既存 Provider Adapter / `model_candidates.toml` / model-recommender prompt との接続点を先に確定し、programmer が迷わず実装できる状態にする。

## 完了条件

- Markdown / JSON の最小出力スキーマが確定している。
- CPU / メモリ / GPU / OS の取得方針が macOS / Linux 前提で整理され、標準ライブラリのみで成立する実装方針になっている。
- 設定済み Provider への疎通確認と `model_candidates.toml` に列挙されたモデル可用性確認の責務境界が定義されている。
- `system-probe` と既存 `check`、TASK-00013 側で扱う config lint / dry-run の責務差分が整理されている。
- 必要な ID (FUN- / CLI- / CFG- / PVD- / NFR- など) が採番され、関連する `docs/` に反映されている。
- 実装・README・レビューに必要な影響範囲が列挙されている。

## スコープ外

- `system-probe` の実装とテスト (TASK-00012-02)
- README 更新 (TASK-00012-03)
- 最終レビュー (TASK-00012-04)

## 設計対象

- `local-llm-benchmark system-probe` の責務、出力スキーマ、終了状態
- 既存 `check` と将来の `config lint` / `config dry-run` の責務境界
- 既存 Provider Adapter、`model_candidates.toml`、v1.1.0 model-recommender prompt との接続点

## 設計判断

### 1. `system-probe` は `check` とは別サブコマンドにする

| 面 | 結論 |
| --- | --- |
| `check` | 現行互換の静的整合性確認に固定する。設定読込、参照整合、Result Store 書込可否、Comparison 参照検証までを扱う |
| `system-probe` | host facts、provider 到達確認、model ref 解決という外部状態の観測に限定する |
| 将来の `config lint` | `check` を拡張する静的 validation 面とし、provider 通信を持ち込まない |
| 将来の `config dry-run` | `system-probe` の provider 到達確認 / model ref 解決を再利用しつつ、Run 設定と TaskProfile を読んで 1 case の prompt 組立まで進む |

根拠:
- 現行 trunk の `_cmd_check` は `load_config_bundle` / `check_bundle` / `check_comparison` のみを呼び、provider 通信や hardware 収集を行っていない。
- `system-probe` は CPU / メモリ / GPU / OS と provider 外部状態を扱うため、静的 validation と混ぜると終了コードと出力意味がぶれる。

### 2. 出力スキーマは JSON 一次、Markdown 派生で固定する

- 最小 JSON セクションは `system`, `providers`, `model_candidates`, `summary` の 4 つに固定する。
- `system` は model-recommender prompt の必須ヒアリング項目のうち、provider 以外の自動取得可能部分を直接転記できる粒度にする。
- `providers` は到達状態と probe 根拠、`model_candidates` は `provider_model_ref` 単位の可用性状態 (`available` / `missing` / `unknown`) を持つ。
- Markdown は同じ 4 セクションを同順で再構成し、人間が 1 画面で確認できる形にする。

### 3. `model_candidates.toml` と Provider Adapter の結合点を明示する

- `system-probe` の設定入力は `model_candidates.toml` と `providers.toml` に限定する。TaskProfile / Run / Comparison は不要。
- 可用性判定の比較キーは `ModelCandidate.provider_model_ref` とする。
- provider 固有 endpoint や inventory API は Provider Adapter 内に閉じ、上位層は「到達確認」と「model ref 解決」だけを扱う。

### 4. 取得方針は macOS / Linux の best-effort とする

- OS / CPU / 論理コア / 物理コア / 総メモリは Python 標準ライブラリと OS 標準の情報源で取得する。
- GPU は macOS / Linux とも best-effort とし、標準ライブラリから `subprocess` で OS 標準コマンドを呼ぶ方式を許容する。コマンドが存在しない場合は `unknown` で返す。
- host facts の欠損は `system-probe` の内部失敗ではなく「未観測」として扱い、provider / model の probe を継続する。

## 影響範囲

- programmer は [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md) を正本として実装する。
- reviewer は `check` 非拡張、`system-probe` の 4 セクション出力、`config lint` / `dry-run` との責務分離を確認する。
- docs-writer は README 更新時に `check` と `system-probe` を別用途で説明し、`config lint` / `dry-run` を future scope として誤混同しない。

## 残課題

- 将来の TASK-00013 で `config lint` を新しい public surface として追加するか、`check` を互換 alias として残すかの名称整理は未確定。意味上の責務境界のみ本 task で確定した。
- GPU 取得の具体コマンド優先順位 (macOS / Linux) は実装 task で決め、NFR-00302 の範囲でテストと合わせて確定する。

## 進捗ログ

- 2026-04-22 project-master: 起票。現行 trunk では `check` が設定検証を担っているため、`system-probe` と config lint の責務境界整理も合わせて依頼
- 2026-04-22 solution-architect: Status を `in-progress` として着手。`README.md`、`docs/design/05-cli-surface.md`、`src/local_llm_benchmark/cli/main.py` の `_cmd_check`、`src/local_llm_benchmark/config/loader.py`、`configs/model_candidates.toml`、`.github/prompts/model-recommender.prompt.md`、TASK-00011-01、TASK-00012、TASK-00013 を確認し、`check` は静的整合性確認に限定されていることを確認した。
- 2026-04-22 solution-architect: [docs/requirements/02-functional.md](docs/requirements/02-functional.md), [docs/design/02-components.md](docs/design/02-components.md), [docs/design/04-workflows.md](docs/design/04-workflows.md), [docs/design/05-cli-surface.md](docs/design/05-cli-surface.md), [docs/design/06-configuration-sources.md](docs/design/06-configuration-sources.md), [docs/design/07-provider-contract.md](docs/design/07-provider-contract.md), [docs/development/release-criteria.md](docs/development/release-criteria.md) を更新。FUN-00404 / FUN-00405, CLI-00109 / CLI-00307, CFG-00601〜00603, PVD-00004 / PVD-00106〜00107 / PVD-00209〜00211 / PVD-00406, FLW-00007 を採番し、`system-probe` を動的観測、`check` を静的検証、将来の `config lint` / `dry-run` をその周辺責務として整理した。
- 2026-04-22 solution-architect: 完了条件を満たしたため Status を `review-pending` に更新。programmer は CLI / workflow / config / provider の 4 文書を合わせて参照し、reviewer は `check` 非拡張と model-recommender prompt への転記粒度を重点確認する。
- 2026-04-23 solution-architect: [progress/reviewer/TASK-00012-05-review-system-probe-design.md](progress/reviewer/TASK-00012-05-review-system-probe-design.md) の合格を確認。差し戻しなしで設計確定とし、Status を `done` に更新した。

## レビュー記録 (reviewer 用)

- 2026-04-23 reviewer: [progress/reviewer/TASK-00012-05-review-system-probe-design.md](progress/reviewer/TASK-00012-05-review-system-probe-design.md) で合格。差し戻し事項なし。
