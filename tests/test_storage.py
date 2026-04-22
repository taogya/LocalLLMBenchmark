"""Result Store のユニットテスト.

対応 ID: FUN-00206, ARCH-00204, NFR-00103, NFR-00204, DAT-00201
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from local_llm_benchmark import SCHEMA_VERSION
from local_llm_benchmark.models import CaseAggregation, RunSummary, Trial
from local_llm_benchmark.storage import ResultStore, generate_run_id


class TestRunIdGeneration(unittest.TestCase):
    def test_format(self) -> None:
        ts = datetime(2026, 4, 19, 12, 34, 56, tzinfo=timezone.utc)
        rid = generate_run_id("qwen2:1.5b", now=ts)
        self.assertTrue(rid.startswith("run-20260419-123456-"))
        self.assertIn("qwen2_1.5b", rid)


class TestWriteRun(unittest.TestCase):
    def test_atomic_write_and_layout(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            trial = Trial(
                task_profile_name="tp",
                case_name="c1",
                model_name="m",
                sequence=1,
                response_text="ok",
                elapsed_seconds=0.1,
                input_tokens=3,
                output_tokens=5,
                quality_score=1.0,
                failure_kind=None,
                failure_detail=None,
            )
            agg = CaseAggregation(
                task_profile_name="tp",
                case_name="c1",
                model_name="m",
                n=1,
                score_mean=1.0,
                score_p50=1.0,
                score_p95=1.0,
                latency_mean=0.1,
                latency_p50=0.1,
                latency_p95=0.1,
                output_tokens_mean=5.0,
                failure_count=0,
                failures_by_kind={},
            )
            summary = RunSummary(
                model_name="m",
                score_mean=1.0,
                latency_mean=0.1,
                output_tokens_mean=5.0,
                success_trials=1,
                failure_trials=0,
            )
            run_id = "run-test-1"
            run_dir = store.write_run(
                run_id=run_id,
                meta={
                    "started_at": "2026-04-19T00:00:00+00:00",
                    "model_candidate": {"name": "m"},
                    "provider_identity": {"kind": "ollama"},
                    "generation_conditions": {"temperature": 0.0},
                },
                trials=[trial],
                aggregations=[agg],
                run_summary=summary,
            )
            # ARCH-00204: 完成ディレクトリが残り、partial は残らない
            self.assertTrue(run_dir.is_dir())
            self.assertFalse((Path(td) / f"{run_id}.partial").exists())
            # NFR-00103: 生応答 (raw/) と集計値 (aggregation.json) が分離
            self.assertTrue((run_dir / "meta.json").is_file())
            self.assertTrue((run_dir / "aggregation.json").is_file())
            self.assertTrue((run_dir / "raw" / "trials.jsonl").is_file())
            # NFR-00204 / DAT-00201: 版識別子
            meta = json.loads((run_dir / "meta.json").read_text("utf-8"))
            self.assertEqual(meta["schema_version"], SCHEMA_VERSION)
            self.assertEqual(meta["run_id"], run_id)
            # JSONL: 1 行 1 trial
            with (run_dir / "raw" / "trials.jsonl").open("r", encoding="utf-8") as f:
                lines = [ln for ln in f if ln.strip()]
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual(row["sequence"], 1)

    def test_list_runs_excludes_partial(self) -> None:
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            (Path(td) / "run-a").mkdir()
            (Path(td) / "run-b.partial").mkdir()
            self.assertEqual(store.list_runs(), ["run-a"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
