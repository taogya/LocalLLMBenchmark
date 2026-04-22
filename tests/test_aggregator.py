"""Trial Aggregator のユニットテスト.

対応 ID: FUN-00303, NFR-00101, SCR-00401..00405, SCR-00501..00503, DAT-00106
"""

from __future__ import annotations

import unittest

from local_llm_benchmark.models import Trial
from local_llm_benchmark.orchestration.aggregator import (
    _percentile_linear,
    aggregate_case,
    aggregate_run,
)


def _trial(
    seq: int,
    score: float | None = 1.0,
    elapsed: float | None = 0.5,
    out_tokens: int | None = 10,
    failure_kind: str | None = None,
) -> Trial:
    return Trial(
        task_profile_name="tp",
        case_name="c1",
        model_name="m1",
        sequence=seq,
        response_text=None if failure_kind else "x",
        elapsed_seconds=elapsed,
        input_tokens=None,
        output_tokens=out_tokens,
        quality_score=score,
        failure_kind=failure_kind,
        failure_detail="x" if failure_kind else None,
    )


class TestPercentile(unittest.TestCase):
    def test_single(self) -> None:
        self.assertEqual(_percentile_linear([3.0], 0.5), 3.0)

    def test_p50_linear(self) -> None:
        self.assertAlmostEqual(_percentile_linear([1.0, 2.0, 3.0], 0.5), 2.0)
        # 偶数件: 線形補間
        self.assertAlmostEqual(_percentile_linear([1.0, 2.0, 3.0, 4.0], 0.5), 2.5)

    def test_p95(self) -> None:
        self.assertAlmostEqual(
            _percentile_linear([1.0, 2.0, 3.0, 4.0, 5.0], 0.95), 4.8
        )


class TestAggregateCase(unittest.TestCase):
    """SCR-00401..405 / SCR-00501..503."""

    def test_all_success(self) -> None:
        trials = [
            _trial(1, score=1.0, elapsed=0.4, out_tokens=10),
            _trial(2, score=0.0, elapsed=0.6, out_tokens=20),
            _trial(3, score=1.0, elapsed=0.5, out_tokens=15),
        ]
        agg = aggregate_case(trials)
        self.assertEqual(agg.n, 3)
        self.assertAlmostEqual(agg.score_mean or 0.0, 2 / 3)
        self.assertAlmostEqual(agg.latency_mean or 0.0, 0.5)
        self.assertEqual(agg.failure_count, 0)

    def test_failures_excluded_from_n(self) -> None:
        """SCR-00501: 失敗は母数から除外."""
        trials = [
            _trial(1, score=1.0, elapsed=0.4, out_tokens=10),
            _trial(2, failure_kind="timeout"),
            _trial(3, score=0.0, elapsed=0.6, out_tokens=20),
        ]
        agg = aggregate_case(trials)
        self.assertEqual(agg.n, 2)
        self.assertEqual(agg.failure_count, 1)
        self.assertEqual(agg.failures_by_kind, {"timeout": 1})

    def test_all_failed_returns_missing(self) -> None:
        """SCR-00502: 全失敗時は欠損."""
        trials = [
            _trial(1, failure_kind="timeout"),
            _trial(2, failure_kind="timeout"),
        ]
        agg = aggregate_case(trials)
        self.assertEqual(agg.n, 0)
        self.assertIsNone(agg.score_mean)
        self.assertIsNone(agg.latency_mean)


class TestAggregateRun(unittest.TestCase):
    def test_run_summary_from_aggregations(self) -> None:
        trials_a = [_trial(1, score=1.0), _trial(2, score=1.0)]
        trials_b = [
            Trial(
                task_profile_name="tp",
                case_name="c2",
                model_name="m1",
                sequence=1,
                response_text="x",
                elapsed_seconds=1.0,
                input_tokens=None,
                output_tokens=20,
                quality_score=0.0,
                failure_kind=None,
                failure_detail=None,
            ),
        ]
        agg_a = aggregate_case(trials_a)
        agg_b = aggregate_case(trials_b)
        summary = aggregate_run([agg_a, agg_b], "m1")
        self.assertEqual(summary.success_trials, 3)
        self.assertEqual(summary.failure_trials, 0)
        self.assertAlmostEqual(summary.score_mean or 0.0, 0.5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
