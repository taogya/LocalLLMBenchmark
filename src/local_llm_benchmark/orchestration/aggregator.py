"""Trial Aggregator (TASK-00007-01, COMP-00004).

n Trial を CaseAggregation (DAT-00006) に畳み込み、Run サマリ
(DAT-00010) を CaseAggregation のみから導出する (DAT-00106)。

統計値は `statistics` 標準ライブラリで算出する (NFR-00302)。
パーセンタイルは線形補間 (SCR-00403/00404)。
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Iterable, Sequence

from ..models import CaseAggregation, RunSummary, Trial


# ---- パーセンタイル -------------------------------------------------------


def _percentile_linear(values: Sequence[float], p: float) -> float | None:
    """線形補間によるパーセンタイル (SCR-00403/00404).

    `statistics.quantiles` は分位点列を返すため、単一 p に対して直接
    計算するヘルパーを置く。
    - p は 0..1
    - 値が 0 件なら None
    - 値が 1 件ならその値
    """
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    s = sorted(values)
    if p <= 0:
        return float(s[0])
    if p >= 1:
        return float(s[-1])
    rank = p * (len(s) - 1)
    lo = int(rank)
    hi = lo + 1
    if hi >= len(s):
        return float(s[-1])
    frac = rank - lo
    return float(s[lo] + (s[hi] - s[lo]) * frac)


# ---- 集計 ------------------------------------------------------------------


def aggregate_case(trials: Iterable[Trial]) -> CaseAggregation:
    """1 (Case × Model) の Trial 群を CaseAggregation に畳み込む.

    DAT-00104 / SCR-00501: 失敗 Trial は母数 (n) に含めない。
    SCR-00502: 全失敗時は値を欠損 (None) で表現する。
    """
    trials = list(trials)
    if not trials:
        raise ValueError("trial が 0 件: aggregate_case には最低 1 件必要")
    # 同一 (task, case, model) を前提とする
    head = trials[0]
    success = [t for t in trials if t.failure_kind is None]
    failures = [t for t in trials if t.failure_kind is not None]
    failure_kinds = Counter(t.failure_kind for t in failures)

    if not success:
        return CaseAggregation(
            task_profile_name=head.task_profile_name,
            case_name=head.case_name,
            model_name=head.model_name,
            n=0,
            score_mean=None,
            score_p50=None,
            score_p95=None,
            latency_mean=None,
            latency_p50=None,
            latency_p95=None,
            output_tokens_mean=None,
            failure_count=len(failures),
            failures_by_kind=dict(failure_kinds),
        )

    # 品質スコアが None の成功 Trial (採点不可と異なるが念のため除外)
    scores = [float(t.quality_score) for t in success if t.quality_score is not None]
    latencies = [float(t.elapsed_seconds) for t in success if t.elapsed_seconds is not None]
    out_tokens = [float(t.output_tokens) for t in success if t.output_tokens is not None]

    return CaseAggregation(
        task_profile_name=head.task_profile_name,
        case_name=head.case_name,
        model_name=head.model_name,
        n=len(success),
        score_mean=mean(scores) if scores else None,
        score_p50=_percentile_linear(scores, 0.5) if scores else None,
        score_p95=_percentile_linear(scores, 0.95) if scores else None,
        latency_mean=mean(latencies) if latencies else None,
        latency_p50=_percentile_linear(latencies, 0.5) if latencies else None,
        latency_p95=_percentile_linear(latencies, 0.95) if latencies else None,
        output_tokens_mean=mean(out_tokens) if out_tokens else None,
        failure_count=len(failures),
        failures_by_kind=dict(failure_kinds),
    )


def aggregate_run(
    aggregations: Sequence[CaseAggregation],
    model_name: str,
) -> RunSummary:
    """Run サマリを CaseAggregation 群から導出する (DAT-00106).

    Trial 個別値には触らない。
    """
    score_means = [a.score_mean for a in aggregations if a.score_mean is not None]
    latency_means = [a.latency_mean for a in aggregations if a.latency_mean is not None]
    out_tokens_means = [
        a.output_tokens_mean for a in aggregations if a.output_tokens_mean is not None
    ]
    success = sum(a.n for a in aggregations)
    failure = sum(a.failure_count for a in aggregations)
    return RunSummary(
        model_name=model_name,
        score_mean=mean(score_means) if score_means else None,
        latency_mean=mean(latency_means) if latency_means else None,
        output_tokens_mean=mean(out_tokens_means) if out_tokens_means else None,
        success_trials=success,
        failure_trials=failure,
    )
