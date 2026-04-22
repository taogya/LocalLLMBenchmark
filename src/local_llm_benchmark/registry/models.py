"""task_id 00001-03: model registry 用の dataclass。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from local_llm_benchmark.benchmark.models import GenerationSettings


@dataclass(slots=True)
class ModelSpec:
    model_key: str
    provider_id: str
    provider_model_name: str
    capability_tags: tuple[str, ...] = ()
    default_generation: GenerationSettings = field(
        default_factory=GenerationSettings
    )
    metadata: dict[str, Any] = field(default_factory=dict)
