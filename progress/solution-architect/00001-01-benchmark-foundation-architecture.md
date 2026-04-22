---
request_id: "00001"
task_id: "00001-01"
parent_task_id: "00001-00"
owner: "solution-architect"
title: "benchmark-foundation-architecture"
status: "done"
depends_on: []
created_at: "2026-04-17T00:00:00+09:00"
updated_at: "2026-04-17T12:00:00+09:00"
related_paths:
  - "docs/architecture/benchmark-foundation.md"
  - "src"
  - "tests"
---

# 入力要件

- Ollama を起点にしつつ、将来 provider を追加できる benchmark ツール基盤を設計する。
- config 管理、model 管理、prompt 管理の責務境界を整理する。
- 入出力保存は詳細未定のため、必要ならスタブで扱う。

# 整理した要件

- benchmark コアは provider 非依存にする。
- provider adapter と client 層の差し替えポイントを明確にする。
- ディレクトリ構成、主要モジュール、依存方向、最小 dataclass/Protocol を提案する。

# 作業内容

- benchmark core、provider adapter/client、config、model registry、prompt 管理、保存スタブの責務境界を整理した。
- Python 実装担当がそのままスキャフォールドへ落とせるよう、推奨ディレクトリ構成と主要 dataclass/Protocol を設計メモへ記載した。
- Ollama を最初の provider 実装としてどこへ配置し、どこまでを core へ漏らさないかを明示した。

# 判断

- benchmark core は ProviderAdapter、ModelRegistry、PromptRepository、ResultSink の抽象だけへ依存させ、provider 名を知らない構造を採用する。
- provider 実装は adapter と client に分け、adapter が共通 request と共通 response の変換責務を持ち、client が API 通信と raw response 取得を担当する。
- model 情報は config に直書きしすぎず registry で正規化し、prompt は provider 固有設定から切り離した PromptSpec として管理する。
- 保存は ResultSink の最小スタブに留め、永続化形式と集計仕様は後続タスクへ分離する。

# 成果

- docs/architecture/benchmark-foundation.md に初期アーキテクチャメモを追加した。
- 推奨ディレクトリ構成、主要 dataclass/Protocol、依存方向、拡張ポイント、Ollama の位置づけを定義した。
- 実装担当が 00001-03 で最小スキャフォールドを起こすための判断材料を揃えた。

# 設計対象

- provider 非依存の benchmark 実行基盤
- Ollama を最初の実装例とする provider 境界
- config、model registry、prompt 管理、保存スタブの接続点

# 影響範囲

- src 配下の初期パッケージ分割
- tests 配下の単体テスト粒度
- docs 配下の今後の設計メモと導入文書の参照先

# リスク

- model registry と config の責務が実装時に混ざると、設定変更とモデル差し替えの変更理由が分離しにくい。
- provider adapter に例外変換以外の処理を載せすぎると、core が薄くならず差し替えコストが上がる。
- prompt に provider 固有オプションを入れすぎると、比較用 corpus としての再利用性が下がる。

# 改善提案

- 初期実装では静的 registry と in-memory prompt repository から始め、外部ファイル化は Protocol を維持したまま次段階で切り出す。
- raw response と正規化 response を最初から分けた dataclass にしておくと、後続の評価指標や保存形式追加が容易になる。
- ProviderAdapter の共通テストを用意し、将来 provider 追加時に同じ受け入れ条件で確認できるようにすると保守性が上がる。

# 次アクション

- 00001-03 では共通 dataclass/Protocol、static registry、in-memory prompt repository、OllamaAdapter/OllamaClient、ResultSink stub の順で最小実装へ落とし込む。
- 00001-02 では PromptSpec と config レコードの対応関係をこの設計メモに合わせて詰める。

# 関連パス

- docs/architecture/benchmark-foundation.md
- src
- tests
