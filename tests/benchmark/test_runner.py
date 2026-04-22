"""task_id 00001-03, 00004-02, 00006-03, 00009-04: BenchmarkRunner の最小動作確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    GenerationSettings,
    InferenceResponse,
    InferenceUsage,
)
from local_llm_benchmark.benchmark.runner import BenchmarkRunner
from local_llm_benchmark.config.models import ModelSelector
from local_llm_benchmark.prompts.models import (
    EvaluationMetadata,
    PromptSet,
    PromptSpec,
)
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry
from local_llm_benchmark.registry.models import ModelSpec
from local_llm_benchmark.storage.stub import MemoryResultSink


class CapturingAdapter:
    provider_id = "test-provider"

    def __init__(self) -> None:
        self.requests = []

    def infer(self, request):
        self.requests.append(request)
        return InferenceResponse(
            output_text="接続成功です。",
            raw_response={"message": {"content": "接続成功です。"}},
            usage=InferenceUsage(
                prompt_tokens=10,
                completion_tokens=4,
                total_tokens=14,
            ),
            latency_ms=12.5,
        )


class BenchmarkRunnerTest(unittest.TestCase):
    def test_runner_resolves_and_merges_generation(self) -> None:
        adapter = CapturingAdapter()
        registry = InMemoryModelRegistry(
            [
                ModelSpec(
                    model_key="test.default",
                    provider_id="test-provider",
                    provider_model_name="model-a",
                    capability_tags=("local", "chat"),
                    default_generation=GenerationSettings(
                        temperature=0.3,
                        top_p=0.8,
                    ),
                )
            ]
        )
        prompt = PromptSpec(
            prompt_id="smoke.v1",
            version="1",
            category="classification",
            title="疎通確認",
            description="task_id 00001-03, 00004-02, 00006-03: runner test",
            system_message="短く答えてください。",
            user_message="接続確認です。",
            recommended_generation=GenerationSettings(
                temperature=0.1,
                max_tokens=32,
            ),
            tags=("deterministic", "ja"),
            evaluation_metadata=EvaluationMetadata(
                primary_metric="accuracy",
                secondary_metrics=("macro_f1",),
                reference_type="label",
                scorer="exact_match_label",
                expected_output_format="json",
            ),
            output_contract={
                "type": "json_object",
                "required_keys": ["label"],
                "prediction_path": "label",
                "label_space": ["請求", "技術サポート"],
            },
            metadata={
                "task_id": "00006-03",
                "evaluation_reference": {"label": "請求"},
            },
        )
        repository = InMemoryPromptRepository(
            [prompt],
            [
                PromptSet(
                    prompt_set_id="smoke-set",
                    prompt_ids=(prompt.prompt_id,),
                )
            ],
        )
        sink = MemoryResultSink()
        runner = BenchmarkRunner(
            model_registry=registry,
            prompt_repository=repository,
            provider_adapters={"test-provider": adapter},
            result_sink=sink,
        )

        records = runner.run(
            BenchmarkPlan(
                run_id="run-1",
                suite_id="suite-1",
                model_selector=ModelSelector(
                    explicit_model_keys=("test.default",),
                    provider_id="test-provider",
                ),
                prompt_set_ids=("smoke-set",),
                default_generation=GenerationSettings(max_tokens=16, seed=7),
                trace_metadata={"task_id": "00001-03,00004-02"},
            )
        )

        self.assertEqual(1, len(records))
        self.assertEqual("接続成功です。", records[0].response.output_text)
        self.assertEqual(1, len(adapter.requests))
        self.assertEqual(0.1, adapter.requests[0].generation.temperature)
        self.assertEqual(0.8, adapter.requests[0].generation.top_p)
        self.assertEqual(16, adapter.requests[0].generation.max_tokens)
        self.assertEqual(7, adapter.requests[0].generation.seed)
        self.assertEqual(1, len(sink.records))
        snapshot = records[0].request_snapshot
        self.assertEqual(
            "classification",
            snapshot["prompt_snapshot"]["category"],
        )
        self.assertEqual(
            "accuracy",
            snapshot["prompt_snapshot"]["evaluation_metadata_snapshot"][
                "primary_metric"
            ],
        )
        self.assertEqual(
            {"label": "請求"},
            snapshot["evaluation"]["reference_snapshot"],
        )
        self.assertEqual(
            "accuracy",
            snapshot["evaluation"]["conditions"][0]["metric_name"],
        )
        self.assertEqual(
            "macro_f1",
            snapshot["evaluation"]["conditions"][1]["metric_name"],
        )
        self.assertEqual(
            "label",
            snapshot["evaluation"]["conditions"][0]["reference_type"],
        )
        self.assertEqual(2, len(sink.case_evaluations))
        self.assertEqual(
            ["accuracy", "macro_f1"],
            [row["metric_name"] for row in sink.case_evaluations],
        )
        self.assertEqual("run-metrics.v1", sink.run_metrics["schema_version"])
        self.assertEqual(2, len(sink.run_metrics["metrics"]))

    def test_runner_excludes_error_case_from_evaluation_metrics(self) -> None:
        prompt = PromptSpec(
            prompt_id="short-qa.v1",
            version="1",
            category="short_qa",
            title="短答",
            description="task_id 00009-04: error handling",
            system_message="",
            user_message="回答してください。",
            evaluation_metadata=EvaluationMetadata(
                primary_metric="exact_match_rate",
                reference_type="text",
                scorer="exact_match_text",
                expected_output_format="text",
            ),
            metadata={
                "task_id": "00009-04",
                "evaluation_reference": {"text": "17:00"},
            },
        )
        repository = InMemoryPromptRepository(
            [prompt],
            [
                PromptSet(
                    prompt_set_id="short-qa-set",
                    prompt_ids=(prompt.prompt_id,),
                )
            ],
        )
        registry = InMemoryModelRegistry(
            [
                ModelSpec(
                    model_key="missing.adapter",
                    provider_id="missing-provider",
                    provider_model_name="model-b",
                )
            ]
        )
        sink = MemoryResultSink()
        runner = BenchmarkRunner(
            model_registry=registry,
            prompt_repository=repository,
            provider_adapters={},
            result_sink=sink,
        )

        records = runner.run(
            BenchmarkPlan(
                run_id="run-error",
                suite_id="suite-error",
                model_selector=ModelSelector(
                    explicit_model_keys=("missing.adapter",),
                    provider_id="missing-provider",
                ),
                prompt_set_ids=("short-qa-set",),
            )
        )

        self.assertEqual(1, len(records))
        self.assertIsNotNone(records[0].error)
        self.assertEqual([], sink.case_evaluations)
        self.assertEqual([], sink.run_metrics["metrics"])


if __name__ == "__main__":
    unittest.main()
