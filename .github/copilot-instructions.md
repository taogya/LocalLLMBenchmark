# プロジェクトガイドライン

`.github/copilot-instructions.md` は常時適用の最小方針のみを置きます。詳細は対象別の `instructions` と `agents` を参照してください。

## 言語

- 会話、ドキュメント、コミットメッセージ、進行管理は日本語を既定とする。
- API 名、CLI コマンド、ライブラリ名、設定ファイルのキー名など固有名詞は英語のまま扱う。
- コードコメント・CLI ヘルプ・アプリ内メッセージも、外部仕様に縛られない限り日本語を優先する。

## 目的

- 本ツールの中心目的は「ユーザーの PC・用途で最適なローカルモデルを選ぶ」ことです (REQ-00001)。これに寄与しない機能は持ち込まない。
- 詳細は [README.md](../README.md) と [docs/requirements/01-overview.md](../docs/requirements/01-overview.md) を参照。

## ワークフロー

- ユーザー依頼は project-master を入口とし、ロールに委譲する (ROLE-00001)。
- 各ロールの責務と依頼経路は [docs/development/roles.md](../docs/development/roles.md) を正本とする。
- 進行管理は [docs/development/progress.md](../docs/development/progress.md) と [.github/instructions/progress-tracking.instructions.md](instructions/progress-tracking.instructions.md) に従う。
- ID 採番は [docs/development/traceability.md](../docs/development/traceability.md) と [.github/instructions/traceability.instructions.md](instructions/traceability.instructions.md) に従う。

## 設計と実装の関係

- 設計確定 (該当 task が `done`) を実装着手の前提とする (PROG-00103)。
- 設計と実装に齟齬が生じた場合、まず設計側で更新可否を判断する。実装は設計に追従する。
- 設計書は実装と密になる具体記述 (クラス名・関数シグネチャ等) を持たない。実装に踏み込んだ記述が必要な場合は実装側コメントで対応する。

## 調査

- 一次情報 (公式ドキュメント、公式リポジトリ、メンテナ実装) を優先する。
- 補助記事を使う場合は一次情報で裏取りする。
- 情報源が競合する場合は採用理由を短く明示する。

## 納品

- 前提と未解決事項は短く明示する。
- 求められていない長い背景説明は加えない。
- ユーザー要件をそのまま全採用しない。プロジェクトの中心目的に寄与する部分だけを残す。
- ユーザー報告では、関連したドキュメント・ファイルのパスを示す。
