# TASK-00003-01 設計ドキュメント 6 件追加

- Status: review-pending
- Role: solution-architect
- Parent: TASK-00003
- Related IDs: REQ-00001, FUN-001xx〜004xx, NFR-00001〜00602, ARCH-00001〜00302, COMP-00001〜00009, DAT-00001〜00202

## 目的

実装着手の前提となる以下 6 件を作成し、既存設計 (`docs/requirements/`, `docs/design/01-04`, `docs/development/`) と整合させる。

## 成果物

1. `docs/design/05-cli-surface.md`
   - 用途: FUN- を CLI 操作面に写像する。サブコマンド一覧、入力/出力の責務、終了コード方針
   - ID 接頭辞: `CLI-` (新規カテゴリ。`docs/development/traceability.md` と `.github/instructions/traceability.instructions.md` にも追記)
   - 必須内容: FUN-00104/00201/00301/00305/00401/00402 を CLI に対応付けたサブコマンド一覧、ユーザー入力 (引数/ファイル) と出力 (stdout/ファイル) の境界、エラー時の終了コード方針 (NFR-00003)
   - 制約: 関数名・実装ライブラリ名 (例: argparse/click) には踏み込まない

2. `docs/design/06-configuration-sources.md`
   - 用途: Configuration Loader / Task Catalog / Result Store が読む物理ファイル群を定義
   - ID 接頭辞: `CFG-`
   - 必須内容: ファイル種別 (Task Profile 定義, Model Candidate 定義, Run 設定, 認証情報の解決) ごとの所在・所有者・必須/任意項目の概念リスト、BYO データの分離方針 (ARCH-00005)、認証情報の取り扱い (NFR-00401, ARCH-00303)
   - 制約: 具体的な TOML キー名は最小限。実装側コメントで詳細化される前提を明記

3. `docs/design/07-provider-contract.md`
   - 用途: Provider Adapter の概念契約を定義 (COMP-00005, ARCH-00201)
   - ID 接頭辞: `PVD-`
   - 必須内容: 標準化された推論リクエストの項目 (prompt/生成条件/メタ)、レスポンスの項目 (応答テキスト/性能 metric の単位/生応答/失敗種別)、失敗の分類 (provider unreachable, model not found, timeout, malformed response 等)、Ollama を v1 唯一の実装とする前提
   - 制約: HTTP エンドポイント名・関数名には踏み込まない

4. `docs/design/08-scoring-and-ranking.md`
   - 用途: v1 同梱 Quality Scorer の語彙と Ranking 算出規則を定義 (FUN-00302/00304, COMP-00006, COMP-00002)
   - ID 接頭辞: `SCR-`
   - 必須内容:
     - v1 同梱 scorer の一覧 (例: exact_match, regex_match, json_valid, contains, length_within 等。ユーザー用途に必要十分な決定的 scorer を選定)
     - 各 scorer の入出力契約 (期待値の形式、戻り値域)
     - ランキング軸 (品質重視 / 速度重視 / 統合) ごとの算出式とタイブレーカー
     - 統計集計値 (n, mean, p50, p95) の算出方法と欠損 Trial の扱い (DAT-00104)
   - 制約: scorer の Python 実装名には踏み込まない

5. `docs/development/environment.md`
   - 用途: 開発・実行環境の前提と外部依存導入ポリシーを定義
   - ID 接頭辞: 不要 (development 側の運用文書)
   - 必須内容: 対応 OS (NFR-00301), Python バージョン (Python 3.13 を既定), 仮想環境方針 (pyenv + venv), 標準ライブラリ優先 (ARCH-00006, NFR-00302), 外部依存の導入判定 (要件 ID 紐付け、撤去容易性), Ollama を localhost で前提とする旨 (NFR-00402)
   - 制約: 具体的なパッケージ名 (httpx/requests 等) を網羅しない。導入は実装 task で個別判断

6. `docs/development/release-criteria.md`
   - 用途: v1.0.0 リリース受入基準を確定 (README ロードマップを fold)
   - 必須内容: v1.0.0 で満たすべき FUN-/NFR- ID の列挙、検証方法 (smoke 観点)、明示的な未対応 (OOS-)、後段リリース (v1.1, v2.0) との境界
   - 制約: 実装方法・スケジュールには踏み込まない

## 横断作業

- `docs/development/traceability.md` と `.github/instructions/traceability.instructions.md` に新 ID 接頭辞 `CLI-` `CFG-` `PVD-` `SCR-` を追記
- 各新規ドキュメントは冒頭で関連既存 ID を明記
- ID 採番は 5 桁 0 埋め、単調増加

## 進め方

1. 上記 6 ドキュメントを 1 ファイルずつ作成
2. ID 体系更新 (traceability)
3. 既存 docs/design/01-04 と矛盾がないか自己点検
4. 完了条件を満たしたら `Status: review-pending` にする

## 完了条件

- 6 ファイルが作成されている
- ID 体系更新が反映されている
- 既存設計との矛盾が自己点検済み

## 進捗ログ

### 2026-04-19 solution-architect

作成・更新したファイル:

- `docs/design/05-cli-surface.md` (新規)
- `docs/design/06-configuration-sources.md` (新規)
- `docs/design/07-provider-contract.md` (新規)
- `docs/design/08-scoring-and-ranking.md` (新規)
- `docs/development/environment.md` (新規)
- `docs/development/release-criteria.md` (新規)
- `docs/development/traceability.md` (CLI-/CFG-/PVD-/SCR- を追記)
- `.github/instructions/traceability.instructions.md` (CLI-/CFG-/PVD-/SCR- を追記)

採番した ID レンジ:

- CLI-00001〜CLI-00004 (設計原則), CLI-00101〜CLI-00105 (サブコマンド), CLI-00201〜CLI-00204 (出力切替), CLI-00301〜CLI-00305 (終了コード), CLI-00401〜CLI-00403 (失敗表示)
- CFG-00001〜CFG-00004 (設計原則), CFG-00101〜CFG-00106 (ファイル種別), CFG-00201〜CFG-00205 (項目), CFG-00301〜CFG-00303 (BYO 分離), CFG-00401〜CFG-00404 (認証), CFG-00501〜CFG-00505 (整合性検証)
- PVD-00001〜PVD-00003 (設計原則), PVD-00101〜PVD-00105 (リクエスト), PVD-00201〜PVD-00208 (レスポンス), PVD-00301〜PVD-00307 (失敗種別), PVD-00401〜PVD-00404 (v1 前提)
- SCR-00001〜SCR-00004 (設計原則), SCR-00101〜SCR-00107 (scorer 語彙), SCR-00201〜SCR-00203 (共通規約), SCR-00301〜SCR-00302 (追加ルール), SCR-00401〜SCR-00405 (集計), SCR-00501〜SCR-00503 (欠損), SCR-00601〜SCR-00607 (ランキング軸と重み), SCR-00701 (タイブレーカー), SCR-00801 (性能正規化)

自己点検結果:

- ARCH-/COMP-/DAT-/FLW- との依存方向 (Presentation → Orchestration → Measurement → Configuration & Storage) を逆転する記述なし
- ARCH-00003 (機械可読が一次) と CLI-00201 が一致
- DAT-00104 (成功 Trial のみ集計) と SCR-00501 が一致
- DAT-00105 (生成条件は Run 内固定) と PVD-00102 / CFG-00203 が一致
- NFR-00401 / ARCH-00303 と CFG-00401〜00403 が一致
- 既存 ID の意味変更はなし (新規 ID のみ追加)
- 既存 01-04 への加筆は実施せず、相互参照は新規ドキュメント側からのみ張った

残課題 / 想定リスク:

- ランキング統合軸の重み既定値 (SCR-00605/00606 = 0.7/0.3) は実装着手後の smoke 検証でユーザー体感に照らした再評価が必要
- v1.0.0 の検証 task (release-criteria に基づく単一検証 task) は project-master が別途起票する必要がある
- `partial-failure` 終了コード (CLI-00305) を導入したが、CI 連携は v1 範囲外 (OOS-00008) のため運用側ドキュメントは v1.1 で整備
- environment.md は具体パッケージを列挙しないため、実装 task 起票時に「導入根拠 ID」記載漏れがないか reviewer ロールでの自己点検が必要
