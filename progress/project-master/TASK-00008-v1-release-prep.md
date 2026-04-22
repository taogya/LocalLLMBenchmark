# TASK-00008 v1.0.0 リリース準備

- Status: done
- Role: project-master
- Related IDs: REQ-00001, NFR-00501, FUN-00207, FUN-00308

## 目的

実装フェーズ (TASK-00007 系) で v1.0.0 受入基準を全件通過したため、利用者向けドキュメントを v1.0.0 として整備する。実装本体への変更は伴わない。

## 完了条件

- README.md が v1.0.0 の最短セットアップ〜初回 Run / Compare / Report 手順を提示し、`configs/` サンプルへの導線がある
- CHANGELOG.md が新規作成され、v1.0.0 の主要追加 (8 Component / `run` `compare` `report` `runs` `comparisons` `list` `check` / SCR-00101..00107 / Ollama Provider) と既知の制約 (CLI-00306 予約 / Provider は Ollama のみ) を 1 セクションで網羅
- `docs/development/release-criteria.md` または README に CLI-00306 (`EXIT_COMPARISON_INCOMPLETE`) を「v1.0.0 では予約のみ」と 1 行明記
- `MMDC_REQUIRED=1 bash scripts/verify.sh` 全 OK

## 子 task

- TASK-00008-01 docs-writer: README v1.0.0 整備 + CHANGELOG 新規作成 + CLI-00306 予約注記 (done)
- TASK-00008-02 docs-writer: README からトレース ID 除去 + store-root パス見直し (done)

## 残課題 (本 task のスコープ外)

- v1.0.0 Git タグ付け (`git tag v1.0.0` + push) — ユーザーが手動で実施
- `tmp/results/` 残骸掃除 (gitignore 済のためリポジトリには影響なし、対応不要)

## 進捗ログ

- 2026-04-20 project-master: 親 task 起票、TASK-00008-01 を docs-writer に委譲
- 2026-04-20 docs-writer/reviewer: TASK-00008-01 完了 (README v1.0.0 整備 + CHANGELOG 新規作成)
- 2026-04-20 project-master: pyproject.toml version `1.0.0.dev0` → `1.0.0` に確定
- 2026-04-20 project-master: ユーザー指摘 (README にトレース ID 混入 / store-root が不適切) を受け TASK-00008-02 を起票
- 2026-04-20 docs-writer/reviewer: TASK-00008-02 完了 (README/configs/README から ID 約 41 件除去、store-root を `./results` に変更し自動 mkdir を明記)
- 2026-04-20 project-master: 親 task クローズ。Git タグ付けはユーザーに引き渡し
