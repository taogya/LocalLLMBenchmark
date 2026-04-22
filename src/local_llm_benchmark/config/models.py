"""task_id 00001-03, 00004-02: 共通設定 dataclass 群。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from local_llm_benchmark.benchmark.models import GenerationSettings
from local_llm_benchmark.prompts.models import PromptSet, PromptSpec
from local_llm_benchmark.registry.models import ModelSpec


@dataclass(slots=True)
class ProviderProfile:
    provider_id: str
    connection: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelSelector:
    explicit_model_keys: tuple[str, ...] = ()
    include_tags: tuple[str, ...] = ()
    provider_id: str | None = None


@dataclass(slots=True)
class BenchmarkSuiteConfig:
    suite_id: str
    description: str
    model_selector: ModelSelector
    prompt_set_ids: tuple[str, ...] = ()
    prompt_ids: tuple[str, ...] = ()
    generation_overrides: GenerationSettings = field(
        default_factory=GenerationSettings
    )
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppConfig:
    provider_profiles: dict[str, ProviderProfile]
    benchmark_suites: dict[str, BenchmarkSuiteConfig]


@dataclass(slots=True)
class ConfigBundle:
    app_config: AppConfig
    model_specs: tuple[ModelSpec, ...] = ()
    prompt_specs: tuple[PromptSpec, ...] = ()
    prompt_sets: tuple[PromptSet, ...] = ()
