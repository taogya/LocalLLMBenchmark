"""Report Renderer のユニットテスト (TASK-00007-02).

対応 ID: FUN-00308, FUN-00305, FUN-00307, COMP-00012, NFR-00004, NFR-00302
"""

from __future__ import annotations

import unittest

from local_llm_benchmark.reporting import (
    render_comparison_markdown,
    render_run_markdown,
)


class TestRunMarkdown(unittest.TestCase):
    def test_render_contains_summary_and_cases(self) -> None:
        meta = {
            "run_id": "run-X",
            "started_at": "2026-04-20T00:00:00+00:00",
            "model_candidate": {
                "name": "A",
                "provider_kind": "ollama",
                "provider_model_ref": "stub:A",
            },
            "task_profiles": ["qa"],
            "n_trials": 3,
            "generation_conditions": {
                "temperature": 0.0, "seed": 42, "max_tokens": 16
            },
        }
        agg = {
            "run_summary": {
                "score_mean": 0.9, "latency_mean": 0.5,
                "output_tokens_mean": 10.0, "success_trials": 3,
                "failure_trials": 0,
            },
            "case_aggregations": [
                {
                    "task_profile_name": "qa",
                    "case_name": "c1",
                    "n": 3,
                    "score_mean": 0.9,
                    "score_p50": 1.0,
                    "score_p95": 1.0,
                    "latency_mean": 0.5,
                    "latency_p95": 0.6,
                    "failure_count": 0,
                }
            ],
        }
        out = render_run_markdown(meta, agg)
        self.assertIn("# Run レポート: run-X", out)
        self.assertIn("モデルサマリ", out)
        self.assertIn("Case 別集計", out)
        self.assertIn("0.9000", out)  # score_mean
        self.assertIn("0.5000 s", out)  # latency 表示


class TestComparisonMarkdown(unittest.TestCase):
    def _payload(self) -> dict:
        return {
            "comparison_id": "cmp-X",
            "created_at": "2026-04-20T00:00:00+00:00",
            "run_ids": ["run-A", "run-B"],
            "ranking_axis_default": "integrated",
            "weights": {"w_quality": 0.7, "w_speed": 0.3},
            "report": {
                "task_profile_names": ["qa"],
                "per_model": [
                    {
                        "model_name": "A", "run_id": "run-A",
                        "quality_mean": 0.9, "quality_p50": 1.0,
                        "latency_mean": 1.0, "latency_p95": 1.0,
                        "output_tokens_mean": 10.0,
                        "speed_subscore": 0.5, "integrated_score": 0.78,
                        "success_trials": 3, "failure_trials": 0,
                    },
                    {
                        "model_name": "B", "run_id": "run-B",
                        "quality_mean": 0.5, "quality_p50": 0.5,
                        "latency_mean": 0.5, "latency_p95": 0.5,
                        "output_tokens_mean": 8.0,
                        "speed_subscore": 1.0, "integrated_score": 0.65,
                        "success_trials": 3, "failure_trials": 0,
                    },
                ],
                "ranking_quality": [
                    {"rank": 1, "model_name": "A", "run_id": "run-A", "value": 0.9},
                    {"rank": 2, "model_name": "B", "run_id": "run-B", "value": 0.5},
                ],
                "ranking_speed": [
                    {"rank": 1, "model_name": "B", "run_id": "run-B", "value": 0.5},
                    {"rank": 2, "model_name": "A", "run_id": "run-A", "value": 1.0},
                ],
                "ranking_integrated": [
                    {"rank": 1, "model_name": "A", "run_id": "run-A", "value": 0.78},
                    {"rank": 2, "model_name": "B", "run_id": "run-B", "value": 0.65},
                ],
            },
        }

    def test_three_rankings_are_present(self) -> None:
        out = render_comparison_markdown(self._payload())
        self.assertIn("ランキング: 品質重視", out)
        self.assertIn("ランキング: 速度重視", out)
        self.assertIn("ランキング: 統合", out)
        # 入力 Run と重みが見える
        self.assertIn("run-A", out)
        self.assertIn("w_quality=0.7", out)
        # 値が表示されている
        self.assertIn("0.7800", out)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
