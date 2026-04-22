"""task_id 00001-03: benchmark core が依存する抽象境界。"""

from __future__ import annotations

from typing import Protocol, Sequence

from local_llm_benchmark.config.models import ModelSelector
from local_llm_benchmark.prompts.models import PromptSet, PromptSpec
from local_llm_benchmark.registry.models import ModelSpec


class ModelRegistry(Protocol):
    def get(self, model_key: str) -> ModelSpec:
        ...

    def list(self, provider_id: str | None = None) -> list[ModelSpec]:
        ...

    def resolve_selector(self, selector: ModelSelector) -> list[ModelSpec]:
        ...


class PromptRepository(Protocol):
    def get(self, prompt_id: str) -> PromptSpec:
        ...

    def list(self, category: str | None = None) -> list[PromptSpec]:
        ...

    def get_set(self, prompt_set_id: str) -> PromptSet:
        ...

    def resolve_prompt_ids(
        self,
        prompt_ids: Sequence[str],
    ) -> list[PromptSpec]:
        ...

    def resolve_prompt_set_ids(
        self,
        prompt_set_ids: Sequence[str],
    ) -> list[PromptSpec]:
        ...
