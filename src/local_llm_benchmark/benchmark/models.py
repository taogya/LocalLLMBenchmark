"""task_id 00001-03, 00001-08: benchmark core で共有する dataclass 群。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from local_llm_benchmark.config.models import ModelSelector
    from local_llm_benchmark.prompts.models import PromptSpec
    from local_llm_benchmark.registry.models import ModelSpec


@dataclass(slots=True)
class GenerationSettings:
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    stop: tuple[str, ...] = ()

    def __init__(
        self,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        seed: int | None = None,
        stop: Sequence[str] = (),
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed
        self.stop = tuple(stop)

    def merged_with(
        self,
        override: GenerationSettings | None,
    ) -> GenerationSettings:
        if override is None:
            return GenerationSettings(
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                seed=self.seed,
                stop=self.stop,
            )
        return GenerationSettings(
            temperature=(
                override.temperature
                if override.temperature is not None
                else self.temperature
            ),
            top_p=override.top_p if override.top_p is not None else self.top_p,
            max_tokens=(
                override.max_tokens
                if override.max_tokens is not None
                else self.max_tokens
            ),
            seed=override.seed if override.seed is not None else self.seed,
            stop=override.stop or self.stop,
        )

    def to_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {}
        if self.temperature is not None:
            snapshot["temperature"] = self.temperature
        if self.top_p is not None:
            snapshot["top_p"] = self.top_p
        if self.max_tokens is not None:
            snapshot["max_tokens"] = self.max_tokens
        if self.seed is not None:
            snapshot["seed"] = self.seed
        if self.stop:
            snapshot["stop"] = list(self.stop)
        return snapshot


@dataclass(slots=True)
class InferenceUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(slots=True)
class BenchmarkPlan:
    run_id: str
    suite_id: str
    model_selector: ModelSelector
    prompt_set_ids: tuple[str, ...] = ()
    prompt_ids: tuple[str, ...] = ()
    default_generation: GenerationSettings = field(
        default_factory=GenerationSettings
    )
    prompt_bindings: dict[str, dict[str, Any]] = field(default_factory=dict)
    trace_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InferenceRequest:
    model: ModelSpec
    prompt: PromptSpec
    generation: GenerationSettings
    prompt_bindings: Mapping[str, Any] = field(default_factory=dict)
    trace_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InferenceResponse:
    output_text: str
    raw_response: dict[str, Any]
    usage: InferenceUsage | None = None
    latency_ms: float | None = None
    finish_reason: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkRecord:
    run_id: str
    case_id: str
    model_key: str
    prompt_id: str
    request_snapshot: dict[str, Any]
    response: InferenceResponse | None = None
    error: str | None = None
