---
request_id: "00004"
task_id: "00004-01"
parent_task_id: "00004-00"
owner: "solution-architect"
title: "provider-neutral-config-design"
status: "done"
depends_on: []
created_at: "2026-04-17T22:25:00+09:00"
updated_at: "2026-04-17T23:15:00+09:00"
related_paths:
  - "README.md"
  - "src/local_llm_benchmark/config"
  - "src/local_llm_benchmark/cli/main.py"
  - "docs/architecture/prompt-and-config-design.md"
  - ".github/instructions/python-benchmark.instructions.md"
---

# 入力要件

- provider 非依存ファイルから `Ollama` 固有表現を排除する方針を整理する。
- ロードマップ 1 の config 外部化を、3 ランク各 1 モデルの初期比較条件を表現できる形で設計する。
- 必要なら再発防止のルール化も提案する。

# 整理した要件

- provider 固有コマンドや接続語彙は provider 用の入口へ寄せ、共通 CLI や config 抽象には provider 名を漏らさない。
- config 外部化では benchmark suites、model registry、prompt sets、provider profiles の責務を明確にする。
- 3 ランクは将来細分化可能な tier として表現し、ランクごとの代表モデルを設定で持てるようにする。

# 作業内容

- 共通 CLI、config loader、config dataclass、runner、既存テスト、README、architecture docs、progress 親記録を確認し、provider 名が漏れている境界と外部化済みでない責務を特定した。
- docs/architecture/prompt-and-config-design.md に、provider 非依存境界、provider_profiles を含む config 配置、ロードマップ 1 の最小スコープ、3 ランク各 1 モデルの表現、CLI 契約、テスト観点を追記した。
- .github/instructions/python-benchmark.instructions.md に、provider 非依存層へ provider 名を持ち込まない明示ルールを追加した。

# 判断

- src/local_llm_benchmark/cli/main.py は共通層として維持し、実装後は run のような provider 非依存コマンドだけを置く。Ollama 固有の ping や import は providers 配下へ寄せる。
- src/local_llm_benchmark/config/models.py と src/local_llm_benchmark/config/loader.py は共通スキーマと解決器に限定し、provider_id は外部設定から入る不透明な識別子として扱う。Ollama 固有の suite_id、model_key、prompt_id、文言、既定値は持たせない。
- ロードマップ 1 の完了条件は、外部ファイルから benchmark_suites、model_registry、prompt_sets、provider_profiles、prompts を読んで、3 ランク各 1 モデルの baseline suite を generic CLI から実行できる状態と定義した。
- 3 ランク表現は explicit_model_keys で初期 baseline を固定しつつ、model registry の capability tag と metadata で tier 拡張余地を残す方針にした。

# 成果

- programmer がそのまま実装へ移れるように、config 配置、責務分割、CLI 読み方、最小スコープ、テスト観点を docs/architecture/prompt-and-config-design.md へ反映した。
- provider 名の再流入を防ぐため、.github/instructions/python-benchmark.instructions.md に共通層の禁止事項を追加した。
- 自分の担当 task として、request_id 00004 の設計判断を done まで記録した。

# 次アクション

- programmer が共通 CLI の generic run 化、external config loader、provider factory、sample config、関連テストを実装する。
- reviewer が provider 非依存ファイルに provider 固有語が残っていないかと、3 ランク baseline suite の整合性を確認する。

# 関連パス

- README.md
- src/local_llm_benchmark/config
- src/local_llm_benchmark/cli/main.py
- docs/architecture/prompt-and-config-design.md
- .github/instructions/python-benchmark.instructions.md

# 設計対象

- 共通層として扱う CLI 入口と config 層の責務境界。
- ロードマップ 1 の config 外部化で必要になるファイル配置、設定単位、初期 baseline suite の表現。
- provider 固有語の再流入を防ぐための実装ルール。

# 設計判断

- 共通 CLI の責務は、設定の読込、suite 選択、runner への依存注入、結果要約の表示までに限定する。
- provider 固有の import と語彙は providers/<provider_id> 配下の factory、adapter、client、必要なら diagnostics モジュールへ閉じ込める。
- config 配置は benchmark_suites、model_registry、prompt_sets、provider_profiles、prompts の 5 単位に分け、loader は cross-reference の検証と dataclass 変換だけを担当する。
- 初期 3 ランク比較は explicit_model_keys で固定し、将来の細分化は tier tag と metadata の追加で吸収する。

# 影響範囲

- src/local_llm_benchmark/cli/main.py のコマンド構成、help 文言、依存 import。
- src/local_llm_benchmark/config/loader.py と src/local_llm_benchmark/config/models.py の API と外部設定解決フロー。
- 新設される configs 配下のサンプル設定、providers 側の factory、tests/cli と config 周辺のテスト。

# リスク

- provider_profiles を provider_id キー前提で実装すると、同一 provider の複数接続先が必要になった時に追加設計が要る。
- YAML 採用は docs と整合する一方で依存追加が必要になるため、stdlib 優先とのトレードオフを programmer 側で明示して進める必要がある。

# 改善提案

- request 00004 の実装後、README には config root の構成と generic run コマンドだけを短く追記し、詳細は architecture docs へ寄せる。
- 後続 request では providers/factory の dispatch を registry 化し、新 provider 追加時の差分を providers 配下だけで閉じられるようにするとよい。