"""task_id 00001-03: in-memory model registry。"""

from __future__ import annotations

from local_llm_benchmark.config.models import ModelSelector
from local_llm_benchmark.registry.models import ModelSpec


class InMemoryModelRegistry:
    def __init__(self, model_specs: list[ModelSpec]) -> None:
        self._model_specs = {spec.model_key: spec for spec in model_specs}

    def get(self, model_key: str) -> ModelSpec:
        try:
            return self._model_specs[model_key]
        except KeyError as exc:
            raise KeyError(
                f"model_key '{model_key}' は registry に存在しません。"
            ) from exc

    def list(self, provider_id: str | None = None) -> list[ModelSpec]:
        models = list(self._model_specs.values())
        if provider_id is None:
            return models
        return [model for model in models if model.provider_id == provider_id]

    def resolve_selector(self, selector: ModelSelector) -> list[ModelSpec]:
        resolved: list[ModelSpec] = []
        seen: set[str] = set()

        for model_key in selector.explicit_model_keys:
            model = self.get(model_key)
            if (
                selector.provider_id is not None
                and model.provider_id != selector.provider_id
            ):
                continue
            resolved.append(model)
            seen.add(model.model_key)

        tag_filter = set(selector.include_tags)
        for model in self.list(selector.provider_id):
            if model.model_key in seen:
                continue
            if tag_filter and not tag_filter.issubset(
                set(model.capability_tags)
            ):
                continue
            if not selector.explicit_model_keys and not selector.include_tags:
                resolved.append(model)
                seen.add(model.model_key)
                continue
            if selector.include_tags:
                resolved.append(model)
                seen.add(model.model_key)
        return resolved
