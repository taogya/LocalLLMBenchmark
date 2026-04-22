"""task_id 00001-03, 00009-04: suite -> model -> prompt を解決して実行する runner。"""

from __future__ import annotations

from collections.abc import Mapping

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    BenchmarkRecord,
    InferenceRequest,
)
from local_llm_benchmark.benchmark.evaluation import (
    aggregate_run_metrics,
    build_request_snapshot,
    evaluate_record,
)
from local_llm_benchmark.benchmark.protocols import (
    ModelRegistry,
    PromptRepository,
)
from local_llm_benchmark.providers.base import ProviderAdapter
from local_llm_benchmark.storage.base import ResultSink


class BenchmarkRunner:
    def __init__(
        self,
        *,
        model_registry: ModelRegistry,
        prompt_repository: PromptRepository,
        provider_adapters: Mapping[str, ProviderAdapter],
        result_sink: ResultSink,
    ) -> None:
        self._model_registry = model_registry
        self._prompt_repository = prompt_repository
        self._provider_adapters = dict(provider_adapters)
        self._result_sink = result_sink

    def run(self, plan: BenchmarkPlan) -> list[BenchmarkRecord]:
        models = self._model_registry.resolve_selector(plan.model_selector)
        prompts = self._resolve_prompts(plan)

        if not models:
            raise ValueError("BenchmarkPlan からモデルを解決できませんでした。")
        if not prompts:
            raise ValueError("BenchmarkPlan からプロンプトを解決できませんでした。")

        records: list[BenchmarkRecord] = []
        case_evaluations: list[dict[str, object]] = []
        for model in models:
            for prompt in prompts:
                case_id = f"{model.model_key}:{prompt.prompt_id}"
                generation = model.default_generation.merged_with(
                    prompt.recommended_generation
                )
                generation = generation.merged_with(plan.default_generation)
                bindings = plan.prompt_bindings.get(prompt.prompt_id, {})
                snapshot = build_request_snapshot(
                    plan=plan,
                    model=model,
                    prompt=prompt,
                    generation=generation,
                    prompt_bindings=dict(bindings),
                )
                adapter = self._provider_adapters.get(model.provider_id)
                if adapter is None:
                    record = BenchmarkRecord(
                        run_id=plan.run_id,
                        case_id=case_id,
                        model_key=model.model_key,
                        prompt_id=prompt.prompt_id,
                        request_snapshot=snapshot,
                        error=(
                            f"provider adapter '{model.provider_id}' "
                            "が未登録です。"
                        ),
                    )
                    self._result_sink.write(record)
                    records.append(record)
                    continue

                request = InferenceRequest(
                    model=model,
                    prompt=prompt,
                    generation=generation,
                    prompt_bindings=bindings,
                    trace_metadata=plan.trace_metadata,
                )
                try:
                    response = adapter.infer(request)
                    record = BenchmarkRecord(
                        run_id=plan.run_id,
                        case_id=case_id,
                        model_key=model.model_key,
                        prompt_id=prompt.prompt_id,
                        request_snapshot=snapshot,
                        response=response,
                    )
                except Exception as exc:
                    record = BenchmarkRecord(
                        run_id=plan.run_id,
                        case_id=case_id,
                        model_key=model.model_key,
                        prompt_id=prompt.prompt_id,
                        request_snapshot=snapshot,
                        error=str(exc),
                    )
                self._result_sink.write(record)
                records.append(record)
                case_rows = evaluate_record(record)
                if case_rows:
                    self._result_sink.write_case_evaluations(case_rows)
                    case_evaluations.extend(case_rows)

        self._result_sink.write_run_metrics(
            aggregate_run_metrics(
                run_id=plan.run_id,
                records=records,
                case_evaluations=case_evaluations,
            )
        )
        return records

    def _resolve_prompts(self, plan: BenchmarkPlan):
        prompts = self._prompt_repository.resolve_prompt_set_ids(
            plan.prompt_set_ids
        )
        seen_prompt_ids = {prompt.prompt_id for prompt in prompts}
        for prompt in self._prompt_repository.resolve_prompt_ids(
            plan.prompt_ids
        ):
            if prompt.prompt_id not in seen_prompt_ids:
                prompts.append(prompt)
                seen_prompt_ids.add(prompt.prompt_id)
        return prompts
