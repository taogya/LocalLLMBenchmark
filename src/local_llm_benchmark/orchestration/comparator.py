"""Run Comparator (TASK-00007-02, COMP-00011).

複数 Run 識別子を入力に Comparison を生成する.

設計依拠:
- DAT-00009 / DAT-00010 / DAT-00011 (Comparison / RankedItem / ComparisonReport)
- DAT-00108: Comparison は 2 件以上の Run 識別子を保持する
- DAT-00109: 同一 TaskProfile セットを対象とする Run 群のみ束ねる
- DAT-00106: 集計は CaseAggregation 由来 (Trial 個別値に触らない)
- SCR-00802 / 00803 / 00804 / 00805 ランキング軸と統合スコア
- SCR-00806 / 00807 / 00808 重み既定と上書き
- SCR-00809 タイブレーカー
- SCR-00810 性能の正規化方針 (Comparison 内相対正規化)
- FLW-00006 Comparison シーケンス
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Mapping, Sequence

from ..models import (
    Comparison,
    ComparisonReport,
    ComparisonWeights,
    ModelComparisonSummary,
    RANKING_AXES,
    RANKING_AXIS_INTEGRATED,
    RANKING_AXIS_QUALITY,
    RANKING_AXIS_SPEED,
    RankedItem,
)
from ..storage import ResultStore, generate_comparison_id


class ComparisonError(Exception):
    """Run Comparator が検知した不整合 (DAT-00108 / DAT-00109).

    CLI からは user-input error として扱われる (CLI-00302)。
    """


@dataclass
class RunComparator:
    """COMP-00011 Run Comparator.

    Result Store から各 Run の meta + aggregation を読み出し、不変条件を
    検査したうえで Comparison を生成する。
    """

    store: ResultStore

    # ---- 入力検査 (DAT-00108 / DAT-00109) -------------------------------

    def _validate_run_count(self, run_ids: Sequence[str]) -> None:
        # DAT-00108: 2 件以上必須
        unique = list(dict.fromkeys(run_ids))  # 順序維持で重複除去
        if len(unique) < 2:
            raise ComparisonError(
                "Comparison は 2 件以上の Run 識別子が必要 (DAT-00108)。"
                f" 指定: {list(run_ids)}"
            )

    def _load_run_view(self, run_id: str) -> Mapping[str, Any]:
        try:
            meta = self.store.load_meta(run_id)
            agg = self.store.load_aggregation(run_id)
        except FileNotFoundError as exc:
            raise ComparisonError(
                f"指定された Run が Result Store に存在しない: {run_id}"
            ) from exc
        return {"meta": meta, "aggregation": agg}

    def _validate_task_profile_sets(
        self, views: Mapping[str, Mapping[str, Any]]
    ) -> tuple[str, ...]:
        """全 Run の TaskProfile セットが一致することを検証 (DAT-00109).

        戻り値は (一致した場合の) 共通 TaskProfile 名タプル。
        """
        sets: dict[str, frozenset[str]] = {}
        order: dict[str, tuple[str, ...]] = {}
        for run_id, view in views.items():
            names = tuple(view["meta"].get("task_profiles") or ())
            sets[run_id] = frozenset(names)
            order[run_id] = names
        reference = next(iter(sets.values()))
        mismatched = [
            run_id for run_id, s in sets.items() if s != reference
        ]
        if mismatched:
            detail = ", ".join(
                f"{rid}={sorted(sets[rid])}" for rid in views
            )
            raise ComparisonError(
                "Run 群の TaskProfile セットが不一致 (DAT-00109)。"
                f" 詳細: {detail}"
            )
        # 表示用順序は最初の Run のものを採用 (Comparison 内で安定)
        return next(iter(order.values()))

    # ---- サマリ算出 (SCR-00805) -----------------------------------------

    def _per_model_summary(
        self, run_id: str, view: Mapping[str, Any]
    ) -> ModelComparisonSummary:
        """1 Run = 1 ModelCandidate の Comparison 内サマリを作る.

        SCR-00805 1: 品質サブスコア = 当該モデルの全 Case の品質 mean を
        さらに平均する (CaseAggregation のみから導出: DAT-00106)。
        speed_subscore / integrated_score は他モデルとの相対計算後に埋める。
        """
        meta = view["meta"]
        agg = view["aggregation"]
        model = meta.get("model_candidate") or {}
        model_name = str(model.get("name", ""))
        label = model.get("label")

        case_aggs = agg.get("case_aggregations") or []
        score_means = [
            float(c["score_mean"])
            for c in case_aggs
            if c.get("score_mean") is not None
        ]
        score_p50s = [
            float(c["score_p50"])
            for c in case_aggs
            if c.get("score_p50") is not None
        ]
        latency_means = [
            float(c["latency_mean"])
            for c in case_aggs
            if c.get("latency_mean") is not None
        ]
        latency_p95s = [
            float(c["latency_p95"])
            for c in case_aggs
            if c.get("latency_p95") is not None
        ]
        out_tokens_means = [
            float(c["output_tokens_mean"])
            for c in case_aggs
            if c.get("output_tokens_mean") is not None
        ]
        run_summary = agg.get("run_summary") or {}
        return ModelComparisonSummary(
            run_id=run_id,
            model_name=model_name,
            model_label=None if label is None else str(label),
            quality_mean=mean(score_means) if score_means else None,
            quality_p50=mean(score_p50s) if score_p50s else None,
            latency_mean=mean(latency_means) if latency_means else None,
            latency_p95=mean(latency_p95s) if latency_p95s else None,
            output_tokens_mean=(
                mean(out_tokens_means) if out_tokens_means else None
            ),
            success_trials=int(run_summary.get("success_trials") or 0),
            failure_trials=int(run_summary.get("failure_trials") or 0),
            speed_subscore=None,
            integrated_score=None,
        )

    def _apply_speed_and_integrated(
        self,
        per_model: Sequence[ModelComparisonSummary],
        weights: ComparisonWeights,
    ) -> tuple[ModelComparisonSummary, ...]:
        """速度サブスコアと統合スコアを Comparison 内相対で埋める (SCR-00805 2/3).

        - 速度サブスコア = (Comparison 内最速 latency_mean) / 当該 latency_mean
          (最速モデルが 1.0)。latency_mean が無いモデルは None のまま。
        - 統合スコア = wq * 品質サブスコア + ws * 速度サブスコア
          重みは合計 1.0 を強制せず内部で正規化 (SCR-00808)。
          いずれかのサブスコアが None の場合、統合スコアも None 扱い。
        """
        valid_latencies = [
            m.latency_mean for m in per_model if m.latency_mean is not None and m.latency_mean > 0
        ]
        fastest = min(valid_latencies) if valid_latencies else None
        wq = max(0.0, float(weights.w_quality))
        ws = max(0.0, float(weights.w_speed))
        total = wq + ws
        if total <= 0:
            wq_n, ws_n = 0.5, 0.5
        else:
            wq_n, ws_n = wq / total, ws / total
        out: list[ModelComparisonSummary] = []
        for m in per_model:
            if fastest is not None and m.latency_mean and m.latency_mean > 0:
                speed = fastest / m.latency_mean
            else:
                speed = None
            if m.quality_mean is None or speed is None:
                integrated = None
            else:
                integrated = wq_n * m.quality_mean + ws_n * speed
            out.append(
                ModelComparisonSummary(
                    run_id=m.run_id,
                    model_name=m.model_name,
                    model_label=m.model_label,
                    quality_mean=m.quality_mean,
                    quality_p50=m.quality_p50,
                    latency_mean=m.latency_mean,
                    latency_p95=m.latency_p95,
                    output_tokens_mean=m.output_tokens_mean,
                    success_trials=m.success_trials,
                    failure_trials=m.failure_trials,
                    speed_subscore=speed,
                    integrated_score=integrated,
                )
            )
        return tuple(out)

    # ---- ランキング (SCR-00802/00803/00804/00809) -----------------------

    def _rank(
        self,
        per_model: Sequence[ModelComparisonSummary],
        axis: str,
    ) -> tuple[RankedItem, ...]:
        """1 軸ぶんのランキングを算出する.

        欠損 (品質 mean / latency mean / 統合 None) は最下位扱いとして
        ランキング末尾に並べる (SCR-00502 と整合)。タイブレーカーは
        SCR-00809 を Comparison スコープで適用する。
        """
        def primary(m: ModelComparisonSummary) -> tuple[int, float]:
            # 「軸の主要値」を「降順 (品質/統合) または昇順 (速度)」用に符号化
            if axis == RANKING_AXIS_QUALITY:
                v = m.quality_mean
                return (0, -v) if v is not None else (1, 0.0)
            if axis == RANKING_AXIS_SPEED:
                v = m.latency_mean
                return (0, v) if v is not None else (1, 0.0)
            if axis == RANKING_AXIS_INTEGRATED:
                v = m.integrated_score
                return (0, -v) if v is not None else (1, 0.0)
            raise ValueError(f"未知のランキング軸: {axis}")

        def tiebreak(m: ModelComparisonSummary) -> tuple:
            # SCR-00809: 1) 品質 mean 高、2) latency mean 低、3) out tokens mean 低、
            # 4) ModelCandidate 名称 辞書順
            q = -m.quality_mean if m.quality_mean is not None else float("inf")
            lat = m.latency_mean if m.latency_mean is not None else float("inf")
            tok = (
                m.output_tokens_mean
                if m.output_tokens_mean is not None
                else float("inf")
            )
            return (q, lat, tok, m.model_name)

        ordered = sorted(per_model, key=lambda m: (primary(m), tiebreak(m)))
        out: list[RankedItem] = []
        for i, m in enumerate(ordered, start=1):
            if axis == RANKING_AXIS_QUALITY:
                value = m.quality_mean
            elif axis == RANKING_AXIS_SPEED:
                value = m.latency_mean
            else:
                value = m.integrated_score
            out.append(
                RankedItem(
                    rank=i, model_name=m.model_name, run_id=m.run_id, value=value
                )
            )
        return tuple(out)

    # ---- エントリ -------------------------------------------------------

    def build(
        self,
        run_ids: Sequence[str],
        weights: ComparisonWeights | None = None,
        ranking_axis_default: str = RANKING_AXIS_INTEGRATED,
        now: datetime | None = None,
    ) -> Comparison:
        """Comparison を生成する (FLW-00006).

        - DAT-00108: 2 件未満で ComparisonError
        - DAT-00109: TaskProfile セット不一致で ComparisonError
        - 既定軸 / 重みは Comparison メタに記録する (FUN-00310)
        """
        if ranking_axis_default not in RANKING_AXES:
            raise ComparisonError(
                f"未知のランキング軸: {ranking_axis_default}"
                f" (許可: {list(RANKING_AXES)})"
            )
        weights = weights or ComparisonWeights()
        self._validate_run_count(run_ids)
        unique_run_ids = tuple(dict.fromkeys(run_ids))

        views: dict[str, Mapping[str, Any]] = {
            rid: self._load_run_view(rid) for rid in unique_run_ids
        }
        task_profile_names = self._validate_task_profile_sets(views)

        per_model_initial = [
            self._per_model_summary(rid, views[rid]) for rid in unique_run_ids
        ]
        per_model = self._apply_speed_and_integrated(per_model_initial, weights)

        ranking_quality = self._rank(per_model, RANKING_AXIS_QUALITY)
        ranking_speed = self._rank(per_model, RANKING_AXIS_SPEED)
        ranking_integrated = self._rank(per_model, RANKING_AXIS_INTEGRATED)

        comparison_id = generate_comparison_id(unique_run_ids, now=now)
        created_at = (now or datetime.now(timezone.utc)).isoformat()
        report = ComparisonReport(
            comparison_id=comparison_id,
            created_at=created_at,
            run_ids=unique_run_ids,
            task_profile_names=task_profile_names,
            weights=weights,
            ranking_axis_default=ranking_axis_default,
            per_model=per_model,
            ranking_quality=ranking_quality,
            ranking_speed=ranking_speed,
            ranking_integrated=ranking_integrated,
        )
        return Comparison(
            comparison_id=comparison_id,
            created_at=created_at,
            run_ids=unique_run_ids,
            ranking_axis_default=ranking_axis_default,
            weights=weights,
            report=report,
        )
