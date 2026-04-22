"""Run Comparator のユニットテスト (TASK-00007-02).

対応 ID: FUN-00308, FUN-00309, FUN-00310, DAT-00009, DAT-00108, DAT-00109,
        DAT-00110, SCR-00802, SCR-00803, SCR-00804, SCR-00805, SCR-00806,
        SCR-00807, SCR-00808, SCR-00809, NFR-00302
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from local_llm_benchmark.models import (
    CaseAggregation,
    ComparisonWeights,
    RANKING_AXIS_QUALITY,
    RunSummary,
    Trial,
)
from local_llm_benchmark.orchestration import ComparisonError, RunComparator
from local_llm_benchmark.storage import ResultStore


def _write_run(
    store: ResultStore,
    run_id: str,
    *,
    model_name: str,
    task_profiles: list[str],
    score_mean: float,
    latency_mean: float,
    output_tokens_mean: float | None = 5.0,
) -> None:
    """Comparator が読む程度の最小 Run を Result Store に書き込む."""
    case_agg = CaseAggregation(
        task_profile_name=task_profiles[0],
        case_name="c1",
        model_name=model_name,
        n=1,
        score_mean=score_mean,
        score_p50=score_mean,
        score_p95=score_mean,
        latency_mean=latency_mean,
        latency_p50=latency_mean,
        latency_p95=latency_mean,
        output_tokens_mean=output_tokens_mean,
        failure_count=0,
        failures_by_kind={},
    )
    summary = RunSummary(
        model_name=model_name,
        score_mean=score_mean,
        latency_mean=latency_mean,
        output_tokens_mean=output_tokens_mean,
        success_trials=1,
        failure_trials=0,
    )
    trial = Trial(
        task_profile_name=task_profiles[0],
        case_name="c1",
        model_name=model_name,
        sequence=1,
        response_text="ok",
        elapsed_seconds=latency_mean,
        input_tokens=1,
        output_tokens=int(output_tokens_mean or 0),
        quality_score=score_mean,
        failure_kind=None,
        failure_detail=None,
    )
    store.write_run(
        run_id=run_id,
        meta={
            "started_at": "2026-04-20T00:00:00+00:00",
            "model_candidate": {
                "name": model_name,
                "provider_kind": "stub",
                "provider_model_ref": f"stub:{model_name}",
                "label": None,
            },
            "task_profiles": task_profiles,
            "n_trials": 1,
            "generation_conditions": {"temperature": 0.0},
            "provider_identity": {"kind": "stub"},
        },
        trials=[trial],
        aggregations=[case_agg],
        run_summary=summary,
    )


class TestInvariants(unittest.TestCase):
    def test_dat_00108_requires_two_runs(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            _write_run(
                store, "run-A", model_name="A", task_profiles=["qa"],
                score_mean=1.0, latency_mean=0.1,
            )
            cmp = RunComparator(store=store)
            with self.assertRaises(ComparisonError) as ctx:
                cmp.build(["run-A"])
            self.assertIn("DAT-00108", str(ctx.exception))

    def test_dat_00108_dedups_then_checks(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            _write_run(
                store, "run-A", model_name="A", task_profiles=["qa"],
                score_mean=1.0, latency_mean=0.1,
            )
            cmp = RunComparator(store=store)
            with self.assertRaises(ComparisonError):
                cmp.build(["run-A", "run-A"])

    def test_dat_00109_requires_same_task_profile_set(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            _write_run(
                store, "run-A", model_name="A", task_profiles=["qa"],
                score_mean=1.0, latency_mean=0.1,
            )
            _write_run(
                store, "run-B", model_name="B", task_profiles=["qa", "summary"],
                score_mean=0.5, latency_mean=0.2,
            )
            cmp = RunComparator(store=store)
            with self.assertRaises(ComparisonError) as ctx:
                cmp.build(["run-A", "run-B"])
            self.assertIn("DAT-00109", str(ctx.exception))

    def test_unknown_run_id_is_user_input_error(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            _write_run(
                store, "run-A", model_name="A", task_profiles=["qa"],
                score_mean=1.0, latency_mean=0.1,
            )
            cmp = RunComparator(store=store)
            with self.assertRaises(ComparisonError):
                cmp.build(["run-A", "run-missing"])


class TestRanking(unittest.TestCase):
    def _setup_three(self, td: str) -> RunComparator:
        store = ResultStore(Path(td))
        _write_run(store, "run-A", model_name="A", task_profiles=["qa"],
                   score_mean=0.9, latency_mean=1.0, output_tokens_mean=10.0)
        _write_run(store, "run-B", model_name="B", task_profiles=["qa"],
                   score_mean=0.5, latency_mean=0.5, output_tokens_mean=8.0)
        _write_run(store, "run-C", model_name="C", task_profiles=["qa"],
                   score_mean=1.0, latency_mean=2.0, output_tokens_mean=12.0)
        return RunComparator(store=store)

    def test_three_axis_rankings(self) -> None:
        with TemporaryDirectory() as td:
            cmp = self._setup_three(td)
            comparison = cmp.build(["run-A", "run-B", "run-C"])
            r = comparison.report
            self.assertEqual(
                [it.model_name for it in r.ranking_quality], ["C", "A", "B"]
            )
            self.assertEqual(
                [it.model_name for it in r.ranking_speed], ["B", "A", "C"]
            )
            order = [it.model_name for it in r.ranking_integrated]
            self.assertEqual(order, ["A", "C", "B"])
            top = r.ranking_integrated[0]
            self.assertAlmostEqual(top.value, 0.78, places=6)

    def test_axis_default_is_recorded(self) -> None:
        with TemporaryDirectory() as td:
            cmp = self._setup_three(td)
            comparison = cmp.build(
                ["run-A", "run-B"], ranking_axis_default=RANKING_AXIS_QUALITY
            )
            self.assertEqual(comparison.ranking_axis_default, RANKING_AXIS_QUALITY)

    def test_weight_override_changes_integrated_order(self) -> None:
        with TemporaryDirectory() as td:
            cmp = self._setup_three(td)
            comparison = cmp.build(
                ["run-A", "run-B", "run-C"],
                weights=ComparisonWeights(w_quality=0.1, w_speed=0.9),
            )
            order = [it.model_name for it in comparison.report.ranking_integrated]
            self.assertEqual(order[0], "B")

    def test_persistence_roundtrip(self) -> None:
        with TemporaryDirectory() as td:
            cmp = self._setup_three(td)
            comparison = cmp.build(["run-A", "run-B"])
            store = ResultStore(Path(td))
            store.write_comparison(comparison)
            ids = store.list_comparisons()
            self.assertIn(comparison.comparison_id, ids)
            payload = store.load_comparison(comparison.comparison_id)
            self.assertEqual(
                payload["comparison_id"], comparison.comparison_id
            )
            self.assertEqual(payload["run_ids"], list(comparison.run_ids))
            self.assertIn("ranking_quality", payload["report"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
