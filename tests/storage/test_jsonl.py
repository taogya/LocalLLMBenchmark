"""task_id 00006-03, 00009-04: JSONL ResultSink の保存確認。"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    BenchmarkRecord,
    GenerationSettings,
    InferenceResponse,
    InferenceUsage,
)
from local_llm_benchmark.config.models import ModelSelector
from local_llm_benchmark.storage.jsonl import JsonlResultSink


class JsonlResultSinkTest(unittest.TestCase):
    def test_sink_writes_manifest_records_and_raw_files(self) -> None:
        plan = BenchmarkPlan(
            run_id="jsonl-run-1",
            suite_id="suite-1",
            model_selector=ModelSelector(),
            default_generation=GenerationSettings(temperature=0.0, seed=7),
            trace_metadata={"task_id": "00006-03"},
        )
        record = BenchmarkRecord(
            run_id=plan.run_id,
            case_id="model-a:prompt-1",
            model_key="model-a",
            prompt_id="prompt-1",
            request_snapshot={
                "suite_id": plan.suite_id,
                "provider_id": "provider-a",
                "provider_model_name": "provider-model-a",
                "prompt_snapshot": {
                    "version": "1",
                    "category": "classification",
                    "tags": ["baseline"],
                    "evaluation_metadata_snapshot": {
                        "primary_metric": "accuracy",
                        "secondary_metrics": ["macro_f1"],
                        "reference_type": "label",
                        "scorer": "exact_match_label",
                        "difficulty": "starter",
                        "language": "ja",
                        "expected_output_format": "json",
                    },
                },
                "evaluation": {
                    "expected_output_format": "json",
                    "output_contract_snapshot": {"prediction_path": "label"},
                    "reference_snapshot": {"label": "請求"},
                    "conditions": [
                        {
                            "metric_name": "accuracy",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "mean",
                            "threshold": None,
                            "pass_rule": "case_exact_match",
                            "metric_definition": {"prediction_path": "label"},
                            "evaluation_mode": "auto",
                        }
                    ],
                },
            },
            response=InferenceResponse(
                output_text='{"label":"請求"}',
                raw_response={"provider": "payload"},
                usage=InferenceUsage(
                    prompt_tokens=12,
                    completion_tokens=5,
                    total_tokens=17,
                ),
                latency_ms=15.0,
                finish_reason="stop",
                provider_metadata={"task_id": "00006-03"},
            ),
        )

        with TemporaryDirectory() as temp_dir:
            sink = JsonlResultSink(Path(temp_dir), plan)
            sink.write(record)
            sink.write_case_evaluations(
                [
                    {
                        "schema_version": "case-evaluation.v1",
                        "run_id": plan.run_id,
                        "case_id": record.case_id,
                        "model_key": record.model_key,
                        "prompt_id": record.prompt_id,
                        "prompt_category": "classification",
                        "metric_name": "accuracy",
                        "scorer_name": "exact_match_label",
                        "scorer_version": "v1",
                        "reference_type": "label",
                        "evaluation_mode": "auto",
                        "score": 1.0,
                        "passed": True,
                        "normalized_prediction": "請求",
                        "normalized_reference": "請求",
                        "details": {},
                    }
                ]
            )
            sink.write_run_metrics(
                {
                    "schema_version": "run-metrics.v1",
                    "run_id": plan.run_id,
                    "metrics": [
                        {
                            "scope": {
                                "model_key": record.model_key,
                                "prompt_id": record.prompt_id,
                                "prompt_category": "classification",
                            },
                            "metric_name": "accuracy",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "aggregation": "mean",
                            "value": 1.0,
                            "threshold": None,
                            "passed": None,
                            "sample_count": 1,
                            "evaluation_mode": "auto",
                        }
                    ],
                }
            )
            sink.close()

            run_dir = Path(temp_dir) / plan.run_id
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual("completed", manifest["status"])
            self.assertEqual(1, manifest["record_count"])
            self.assertEqual(
                "case-evaluations.jsonl",
                manifest["layout"]["case_evaluations"],
            )
            self.assertEqual(
                "run-metrics.json",
                manifest["layout"]["run_metrics"],
            )

            lines = (run_dir / "records.jsonl").read_text().splitlines()
            self.assertEqual(1, len(lines))
            serialized = json.loads(lines[0])
            self.assertEqual(
                "benchmark-record.v1",
                serialized["schema_version"],
            )
            self.assertNotIn("raw_response", serialized["response"])
            self.assertIn("raw_response_path", serialized["response"])
            self.assertNotIn("provider_metadata", serialized["response"])
            self.assertEqual(
                "accuracy",
                serialized["request_snapshot"]["evaluation"]["conditions"][0][
                    "metric_name"
                ],
            )

            raw_path = run_dir / serialized["response"]["raw_response_path"]
            raw_payload = json.loads(raw_path.read_text())
            self.assertEqual("provider-a", raw_payload["provider_id"])
            self.assertEqual(
                {"task_id": "00006-03"},
                raw_payload["provider_metadata"],
            )
            self.assertEqual(
                {"provider": "payload"},
                raw_payload["raw_response"],
            )

            case_evaluations = (
                run_dir / "case-evaluations.jsonl"
            ).read_text().splitlines()
            self.assertEqual(1, len(case_evaluations))
            self.assertEqual(
                "accuracy",
                json.loads(case_evaluations[0])["metric_name"],
            )
            run_metrics = json.loads(
                (run_dir / "run-metrics.json").read_text()
            )
            self.assertEqual(plan.run_id, run_metrics["run_id"])
            self.assertEqual(1, len(run_metrics["metrics"]))

    def test_sink_rejects_reusing_existing_run_directory(self) -> None:
        plan = BenchmarkPlan(
            run_id="jsonl-run-3",
            suite_id="suite-3",
            model_selector=ModelSelector(),
        )

        with TemporaryDirectory() as temp_dir:
            first_sink = JsonlResultSink(Path(temp_dir), plan)
            first_sink.close()

            with self.assertRaisesRegex(ValueError, "結果ディレクトリが既に存在"):
                JsonlResultSink(Path(temp_dir), plan)

    def test_sink_writes_error_record_without_response(self) -> None:
        plan = BenchmarkPlan(
            run_id="jsonl-run-2",
            suite_id="suite-2",
            model_selector=ModelSelector(),
        )
        record = BenchmarkRecord(
            run_id=plan.run_id,
            case_id="model-b:prompt-2",
            model_key="model-b",
            prompt_id="prompt-2",
            request_snapshot={"suite_id": plan.suite_id},
            error="adapter missing",
        )

        with TemporaryDirectory() as temp_dir:
            sink = JsonlResultSink(Path(temp_dir), plan)
            sink.write(record)
            sink.close()

            run_dir = Path(temp_dir) / plan.run_id
            serialized = json.loads(
                (run_dir / "records.jsonl").read_text().splitlines()[0]
            )
            self.assertIsNone(serialized["response"])
            self.assertEqual("adapter missing", serialized["error"])
            self.assertFalse(any((run_dir / "raw").iterdir()))
            self.assertEqual(
                "",
                (run_dir / "case-evaluations.jsonl").read_text(),
            )
            run_metrics = json.loads(
                (run_dir / "run-metrics.json").read_text()
            )
            self.assertEqual([], run_metrics["metrics"])
