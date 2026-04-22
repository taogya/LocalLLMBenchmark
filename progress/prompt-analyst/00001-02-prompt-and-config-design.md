---
request_id: "00001"
task_id: "00001-02"
parent_task_id: "00001-00"
owner: "prompt-analyst"
title: "prompt-and-config-design"
status: "done"
depends_on: []
created_at: "2026-04-17T00:00:00+09:00"
updated_at: "2026-04-17T00:00:00+09:00"
related_paths:
  - "docs/architecture/prompt-and-config-design.md"
  - "src"
---

# 入力要件

- 評価データ用の prompt 管理方式を定義する。
- config 管理や model 管理と接続しやすいレコード設計を考える。
- provider 固有表現に寄りすぎない比較用 prompt corpus を意識する。

# 整理した要件

- prompt カテゴリ、system_message、user_message、推奨パラメータ、期待メタデータを整理する。
- 実装に依存しない最小レコード案を用意する。
- 小型モデル比較でも破綻しにくい初期カテゴリ案を出す。

# 作業内容

- docs/architecture/prompt-and-config-design.md を追加し、provider 非依存の prompt corpus 管理方針を整理した。
- prompt category、prompt template record、variables、推奨 generation parameters、tags、評価メタデータの項目設計を定義した。
- benchmark suite、model selection、prompt set、prompt template の接続関係と parameter merge の優先順位を整理した。
- Python 側で扱いやすい dataclass 例と YAML 構造例を設計メモへ記載した。

# 判断

- prompt template には provider 固有情報を入れず、model registry 側へ閉じ込める方が再利用しやすい。
- 小型モデル比較の初期カテゴリは、短入力、単一ターン、出力制約が明確なものに寄せる方が比較が安定する。
- generation parameters は prompt に推奨値を持たせつつ、benchmark suite で上書きできる構造にして公平比較へ対応する。

# 成果

- prompt template record の最小項目と、補助レコードである prompt set、model profile、benchmark suite の役割を定義した。
- benchmark suite -> model selection -> prompt set -> prompt template の解決順を明文化した。
- 実装担当が loader、resolver、設定ファイル構造を起こしやすい最小例を docs に残した。

# 次アクション

- プログラマーは設計メモを基に config loader と suite resolver の責務分割を決める。
- 設計アーキテクトは benchmark コアの設定境界がこのレコード設計と衝突しないか確認する。
- 初期 prompt corpus を作る際は、classification と extraction を先行し、small-model-friendly タグで最小セットを構成する。

# 関連パス

- docs
- src
