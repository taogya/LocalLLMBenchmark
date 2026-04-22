---
description: ".github 配下の copilot-instructions、instructions、agents を作成・更新するときに使う。責務境界の重複を避けるためのルール。"
name: "カスタム定義ガバナンス"
applyTo: ".github/copilot-instructions.md, .github/instructions/**/*.md, .github/agents/**/*.md"
---

# カスタム定義ガバナンス

- `copilot-instructions.md` には常時適用される最小方針のみを置く。タスク固有の手順・特定 provider 前提・個別ワークフロー詳細は書かない。
- `instructions/*.instructions.md` は対象ファイルや特定トピック専用のルールに限定する。エージェントの人格や長い運用手順は書かない。
- `agents/*.agent.md` は役割・担当範囲・使えるツール・進め方・出力形式を書く。プロジェクト全体に常時適用されるルールを重複させない。
- 同じ内容を複数ファイルに書かない。最も責務に近いファイルへ寄せ、他は参照で済ませる。
- `docs/` 配下に正本がある内容 (要件、設計、ロール定義、進行管理規約、ID 体系) は、`.github/` 側では参照に留める。
- description は「いつ使うか」が分かる具体的な日本語にする。
- 新しいエージェントやインストラクションを増やす前に、既存ファイルの拡張で済まないかを確認する。
