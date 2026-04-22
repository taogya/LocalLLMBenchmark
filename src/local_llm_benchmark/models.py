"""共通データ型 (TASK-00007-01 / TASK-00007-02).

設計上の概念エンティティ (DAT-) を最小限のデータ構造で表現する。
- DAT-00001 TaskProfile / DAT-00002 Case
- DAT-00003 ModelCandidate
- DAT-00005 Trial
- DAT-00006 CaseAggregation
- DAT-00008 Run / DAT-00010 RunReport (集計形)
- DAT-00009 Comparison / DAT-00011 ComparisonReport (Phase 2: TASK-00007-02)

実装上のクラス名は設計書には書かれていない (ARCH の方針) ため、
ここで初めて確定する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


# ---- 入力素材 (Configuration 由来) -----------------------------------------


@dataclass(frozen=True)
class Case:
    """1 件の入力 + (該当する場合) 期待出力 (DAT-00002)."""

    name: str
    input_text: str
    expected_output: str | None = None


@dataclass(frozen=True)
class ScorerSpec:
    """評価契約 (TaskProfile から scorer を名前で参照する: ARCH-00202).

    - name: SCR- に登録された scorer 概念名 (例: "exact_match")
    - args: scorer 固有の任意引数
    """

    name: str
    args: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskProfile:
    """ユーザー用途の最小単位 (DAT-00001).

    DAT-00101: 最低 1 件の Case を持つ (Loader 側で検証)。
    """

    name: str
    purpose: str
    scorer: ScorerSpec
    cases: Sequence[Case]
    description: str | None = None


@dataclass(frozen=True)
class ProviderEndpoint:
    """provider 接続情報 (CFG-00104, CFG-00204).

    認証情報は環境変数経由でのみ解決する (CFG-00401)。
    Phase 1 (Ollama) は認証を要求しないため、host/port/timeout のみ。
    """

    kind: str
    host: str = "localhost"
    port: int = 11434
    timeout_seconds: float = 120.0


@dataclass(frozen=True)
class ModelCandidate:
    """比較対象モデル (DAT-00003).

    provider_kind は ProviderEndpoint.kind と一致すること
    (Loader 側で検証)。
    """

    name: str
    provider_kind: str
    provider_model_ref: str
    label: str | None = None


@dataclass(frozen=True)
class GenerationConditions:
    """Run 単位で固定される生成条件 (DAT-00105, FUN-00203).

    Run 開始後に変更しない。
    """

    temperature: float | None = None
    seed: int | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class RunPlan:
    """1 Run の実行計画 (DAT-00008, FUN-00207).

    - model_candidate: 1 件のみ (1 Run = 1 Model: ARCH-00207)
    - task_profiles: 評価対象 Task Profile 群
    - n_trials: 1 Case あたり試行回数 (n >= 1, FUN-00202)
    - conditions: 生成条件
    """

    model_candidate: ModelCandidate
    task_profiles: Sequence[TaskProfile]
    n_trials: int
    conditions: GenerationConditions
    provider_endpoint: ProviderEndpoint


# ---- 推論レイヤ (Provider 契約: PVD-) --------------------------------------


@dataclass(frozen=True)
class InferenceRequest:
    """Run Coordinator が Provider Adapter に渡す論理単位 (PVD-00101..00105)."""

    prompt: str
    generation: GenerationConditions
    model_ref: str
    timeout_seconds: float | None
    # PVD-00105 リクエストメタ (失敗ログ突合用)
    run_id: str
    task_profile_name: str
    case_name: str
    trial_index: int


@dataclass(frozen=True)
class InferenceResponse:
    """Provider Adapter の標準化レスポンス (PVD-00201..00208).

    成功/失敗どちらでも本構造に揃える。失敗時は `failure_kind` を埋め
    response_text などは None になる。
    """

    # 成功時必須
    response_text: str | None
    elapsed_seconds: float | None
    # provider が返す場合のみ
    input_tokens: int | None
    output_tokens: int | None
    # PVD-00205: 生応答 (provider 固有形のまま)
    raw_response: Any
    # PVD-00208: provider 識別 (種別 / 接続先 / モデル参照)
    provider_identity: Mapping[str, Any]
    # 失敗時のみ
    failure_kind: str | None = None
    failure_detail: str | None = None


# ---- Trial / 集計 ----------------------------------------------------------


@dataclass(frozen=True)
class Trial:
    """Run の最小実行単位 (DAT-00005).

    DAT-00102: 必ず 1 件の Case と 1 件の ModelCandidate に属する。
    DAT-00103: 同一 Case × 同一 ModelCandidate 内で sequence 連番。
    """

    task_profile_name: str
    case_name: str
    model_name: str
    sequence: int
    response_text: str | None
    elapsed_seconds: float | None
    input_tokens: int | None
    output_tokens: int | None
    quality_score: float | None
    failure_kind: str | None
    failure_detail: str | None


@dataclass(frozen=True)
class CaseAggregation:
    """1 Case × 1 ModelCandidate の Trial 群を畳み込んだ集計 (DAT-00006).

    SCR-00401..00405 に従う。失敗 Trial は母数 (n) から除外する
    (SCR-00501)。値が欠損する場合は None で表現する (SCR-00502)。
    """

    task_profile_name: str
    case_name: str
    model_name: str
    n: int  # 成功 Trial 数
    score_mean: float | None
    score_p50: float | None
    score_p95: float | None
    latency_mean: float | None
    latency_p50: float | None
    latency_p95: float | None
    output_tokens_mean: float | None
    failure_count: int
    failures_by_kind: Mapping[str, int]


@dataclass(frozen=True)
class RunSummary:
    """Run 全体 (単一 Model) のモデルサマリ (DAT-00010).

    Trial 個別値ではなく CaseAggregation のみから導出する (DAT-00106)。
    """

    model_name: str
    score_mean: float | None
    latency_mean: float | None
    output_tokens_mean: float | None
    success_trials: int
    failure_trials: int


# ---- Comparison 系 (Phase 2: TASK-00007-02) -------------------------------


# ランキング軸 (SCR-00802/00803/00804)
RANKING_AXIS_QUALITY = "quality"
RANKING_AXIS_SPEED = "speed"
RANKING_AXIS_INTEGRATED = "integrated"
RANKING_AXES = (RANKING_AXIS_QUALITY, RANKING_AXIS_SPEED, RANKING_AXIS_INTEGRATED)


@dataclass(frozen=True)
class ComparisonWeights:
    """統合スコアの重み (SCR-00806/00807/00808).

    SCR-00808: 合計 1.0 を強制せず、内部で正規化して使う。
    """

    w_quality: float = 0.7  # SCR-00806 既定
    w_speed: float = 0.3  # SCR-00807 既定


@dataclass(frozen=True)
class ModelComparisonSummary:
    """Comparison 内の 1 ModelCandidate (= 1 Run) のサマリ (DAT-00011 構成要素).

    Trial 個別値ではなく CaseAggregation 群を Comparison 内全 Case で平均
    した値 (DAT-00106 / SCR-00805 1) を保持する。`speed_subscore` と
    `integrated_score` は Run Comparator が他モデルとの相対計算後に埋める。
    """

    run_id: str
    model_name: str
    model_label: str | None
    quality_mean: float | None  # 品質 mean (Comparison 内全 Case 平均)
    quality_p50: float | None  # SCR-00802 副軸
    latency_mean: float | None
    latency_p95: float | None
    output_tokens_mean: float | None
    success_trials: int
    failure_trials: int
    speed_subscore: float | None  # SCR-00805 2 (相対)
    integrated_score: float | None  # SCR-00805 3


@dataclass(frozen=True)
class RankedItem:
    """1 軸 1 モデルの順位エントリ (DAT-00011 構成要素).

    `value` は当該軸でのランキング基準値 (品質: quality_mean,
    速度: latency_mean, 統合: integrated_score)。
    """

    rank: int
    model_name: str
    run_id: str
    value: float | None


@dataclass(frozen=True)
class ComparisonReport:
    """Comparison を人間がレビューする視点で再構成した成果 (DAT-00011).

    モデル別サマリ + 3 軸ランキング (品質 / 速度 / 統合) + 使用重み + 入力
    Run 識別子集合を含む。Trial 個別値には触らない (DAT-00106)。
    """

    comparison_id: str
    created_at: str
    run_ids: tuple[str, ...]
    task_profile_names: tuple[str, ...]
    weights: ComparisonWeights
    ranking_axis_default: str
    per_model: tuple[ModelComparisonSummary, ...]
    ranking_quality: tuple[RankedItem, ...]
    ranking_speed: tuple[RankedItem, ...]
    ranking_integrated: tuple[RankedItem, ...]


@dataclass(frozen=True)
class Comparison:
    """Comparison エンティティ (DAT-00009).

    DAT-00108 / DAT-00109: 2 件以上の Run 識別子 + 同一 TaskProfile セット
    を凍結保持する。生成後は不変 (DAT-00110)。レンダリング時に参照する
    集計は ComparisonReport にまとめて持たせる。
    """

    comparison_id: str
    created_at: str
    run_ids: tuple[str, ...]
    ranking_axis_default: str
    weights: ComparisonWeights
    report: ComparisonReport
