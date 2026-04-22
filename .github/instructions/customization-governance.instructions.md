---
description: ".github 配下の copilot-instructions、instructions、agents、prompts を作成または更新するときに使う。公式の責務境界と粒度を守るためのルール。"
name: "カスタム定義ガバナンス"
applyTo: ".github/copilot-instructions.md, .github/instructions/**/*.md, .github/agents/**/*.md, .github/prompts/**/*.md"
---

# カスタム定義ガバナンス

- .github/copilot-instructions.md は、常時適用される安定した全体方針だけを書く。
- .github/copilot-instructions.md に、タスク固有の手順、特定ベンダー前提、個別ワークフローの詳細を書きすぎない。
- .instructions.md は、対象ファイルや特定トピックにだけ適用したいルールを書く。
- .instructions.md に、エージェントの人格や長い運用手順を書かない。
- .agent.md は、役割、担当範囲、使えるツール、進め方、出力形式を書く。
- .agent.md に、プロジェクト全体へ常時適用されるルールを重複して書きすぎない。
- .prompt.md は任意であり、slash command の入口に明確な価値があるときだけ作る。
- agent を直接選べば十分な運用なら、.prompt.md を置かなくてよい。
- .prompt.md は、実行入口になる短い再利用ワークフローとして書く。
- .prompt.md に、常時適用ルールや agent 本体の説明を重複させすぎない。
- description は、いつ使うかが分かる具体的な日本語にする。
- 役割やルールが複数ファイルにまたがるときは、最も責務に近いファイルへ寄せ、重複は減らす。