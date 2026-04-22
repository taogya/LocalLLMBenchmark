"""task_id 00001-03, 00001-08: in-memory prompt repository。"""

from __future__ import annotations

from collections.abc import Sequence

from local_llm_benchmark.prompts.models import PromptSet, PromptSpec


class InMemoryPromptRepository:
    def __init__(
        self,
        prompt_specs: list[PromptSpec],
        prompt_sets: list[PromptSet] | None = None,
    ) -> None:
        self._prompt_specs = {
            prompt.prompt_id: prompt for prompt in prompt_specs
        }
        self._prompt_sets = {
            prompt_set.prompt_set_id: prompt_set
            for prompt_set in (prompt_sets or [])
        }

    def get(self, prompt_id: str) -> PromptSpec:
        try:
            return self._prompt_specs[prompt_id]
        except KeyError as exc:
            raise KeyError(
                f"prompt_id '{prompt_id}' は repository に存在しません。"
            ) from exc

    def list(self, category: str | None = None) -> list[PromptSpec]:
        prompts = list(self._prompt_specs.values())
        if category is None:
            return prompts
        return [prompt for prompt in prompts if prompt.category == category]

    def get_set(self, prompt_set_id: str) -> PromptSet:
        try:
            return self._prompt_sets[prompt_set_id]
        except KeyError as exc:
            raise KeyError(
                f"prompt_set_id '{prompt_set_id}' は repository に存在しません。"
            ) from exc

    def resolve_prompt_ids(
        self,
        prompt_ids: Sequence[str],
    ) -> list[PromptSpec]:
        return [self.get(prompt_id) for prompt_id in prompt_ids]

    def resolve_prompt_set_ids(
        self,
        prompt_set_ids: Sequence[str],
    ) -> list[PromptSpec]:
        resolved: list[PromptSpec] = []
        seen: set[str] = set()
        for prompt_set_id in prompt_set_ids:
            prompt_set = self.get_set(prompt_set_id)
            candidates = self.resolve_prompt_ids(prompt_set.prompt_ids)
            if prompt_set.include_categories or prompt_set.include_tags:
                for prompt in self._prompt_specs.values():
                    if (
                        prompt_set.include_categories
                        and prompt.category
                        not in prompt_set.include_categories
                    ):
                        continue
                    if prompt_set.include_tags and not set(
                        prompt_set.include_tags
                    ).issubset(set(prompt.tags)):
                        continue
                    candidates.append(prompt)
            for prompt in candidates:
                if prompt.prompt_id in seen:
                    continue
                resolved.append(prompt)
                seen.add(prompt.prompt_id)
        return resolved
