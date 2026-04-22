"""task_id 00007-02: benchmark suite discovery 用の表示ロジック。"""

from __future__ import annotations

from dataclasses import dataclass
import re

from local_llm_benchmark.config.models import (
    BenchmarkSuiteConfig,
    ConfigBundle,
)
from local_llm_benchmark.prompts.models import PromptSpec
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry
from local_llm_benchmark.registry.models import ModelSpec


_TASK_PREFIX_PATTERN = re.compile(r"^task_id\s+\d{5}-\d{2}:\s*")


@dataclass(slots=True)
class SuiteCatalogSummary:
    suite_id: str
    description: str
    model_count: int
    prompt_count: int
    providers: tuple[str, ...]


@dataclass(slots=True)
class ProviderRequirement:
    provider_id: str
    model_identifiers: tuple[str, ...]


@dataclass(slots=True)
class SuiteCatalogDetail:
    suite_id: str
    description: str
    tags: tuple[str, ...]
    prompt_set_ids: tuple[str, ...]
    prompt_count: int
    categories: tuple[str, ...]
    provider_requirements: tuple[ProviderRequirement, ...]


def build_suite_summary_views(
    bundle: ConfigBundle,
) -> list[SuiteCatalogSummary]:
    model_registry = InMemoryModelRegistry(list(bundle.model_specs))
    prompt_repository = InMemoryPromptRepository(
        list(bundle.prompt_specs),
        list(bundle.prompt_sets),
    )
    summaries: list[SuiteCatalogSummary] = []
    for suite_id in sorted(bundle.app_config.benchmark_suites):
        suite = bundle.app_config.benchmark_suites[suite_id]
        resolved_models = model_registry.resolve_selector(suite.model_selector)
        resolved_prompts = _resolve_suite_prompts(prompt_repository, suite)
        providers = tuple(
            requirement.provider_id
            for requirement in _build_provider_requirements(resolved_models)
        )
        summaries.append(
            SuiteCatalogSummary(
                suite_id=suite.suite_id,
                description=_normalize_summary_text(suite.description),
                model_count=len(resolved_models),
                prompt_count=len(resolved_prompts),
                providers=providers,
            )
        )
    return summaries


def build_suite_detail_view(
    bundle: ConfigBundle,
    suite_id: str,
) -> SuiteCatalogDetail:
    try:
        suite = bundle.app_config.benchmark_suites[suite_id]
    except KeyError as exc:
        raise ValueError(
            f"suite_id '{suite_id}' は config bundle に存在しません。"
        ) from exc

    model_registry = InMemoryModelRegistry(list(bundle.model_specs))
    prompt_repository = InMemoryPromptRepository(
        list(bundle.prompt_specs),
        list(bundle.prompt_sets),
    )
    resolved_models = model_registry.resolve_selector(suite.model_selector)
    resolved_prompts = _resolve_suite_prompts(prompt_repository, suite)

    return SuiteCatalogDetail(
        suite_id=suite.suite_id,
        description=_normalize_summary_text(suite.description),
        tags=tuple(sorted(suite.tags)),
        prompt_set_ids=tuple(suite.prompt_set_ids),
        prompt_count=len(resolved_prompts),
        categories=tuple(
            sorted({prompt.category for prompt in resolved_prompts})
        ),
        provider_requirements=_build_provider_requirements(resolved_models),
    )


def render_suite_list(bundle: ConfigBundle, *, config_root: str) -> str:
    summaries = build_suite_summary_views(bundle)
    lines = [f"利用可能な suite: {len(summaries)}"]
    for summary in summaries:
        lines.extend(
            [
                "",
                f"- {summary.suite_id}",
                f"  {summary.description}",
                (
                    f"  {summary.model_count} モデル / "
                    f"{summary.prompt_count} プロンプト / "
                    f"provider: {', '.join(summary.providers)}"
                ),
            ]
        )
    if summaries:
        lines.extend(
            [
                "",
                "次の操作",
                (
                    "- 詳細を確認: local-llm-benchmark suites "
                    f"{summaries[0].suite_id} --config-root {config_root}"
                ),
            ]
        )
    return "\n".join(lines)


def render_suite_detail(
    bundle: ConfigBundle,
    suite_id: str,
    *,
    config_root: str,
) -> str:
    detail = build_suite_detail_view(bundle, suite_id)
    prompt_set_summary = ", ".join(detail.prompt_set_ids) or "なし"
    category_summary = ", ".join(detail.categories) or "なし"
    lines = [
        f"suite: {detail.suite_id}",
        f"概要: {detail.description}",
        f"tags: {', '.join(detail.tags) or 'なし'}",
        "",
        "評価対象",
        f"- prompt set: {prompt_set_summary}",
        f"- resolved prompts: {detail.prompt_count}",
        f"- categories: {category_summary}",
        "",
        "準備するもの",
    ]
    for requirement in detail.provider_requirements:
        identifiers = ", ".join(requirement.model_identifiers) or "なし"
        lines.append(f"- {requirement.provider_id}: {identifiers}")
    lines.extend(
        [
            "",
            "次の操作",
            "- provider 側で上記 model identifier を利用可能にする",
            (
                "- local-llm-benchmark run "
                f"--config-root {config_root} --suite {detail.suite_id}"
            ),
        ]
    )
    return "\n".join(lines)


def _build_provider_requirements(
    resolved_models: list[ModelSpec],
) -> tuple[ProviderRequirement, ...]:
    grouped: dict[str, list[str]] = {}
    for model in resolved_models:
        identifiers = grouped.setdefault(model.provider_id, [])
        if model.provider_model_name not in identifiers:
            identifiers.append(model.provider_model_name)
    return tuple(
        ProviderRequirement(
            provider_id=provider_id,
            model_identifiers=tuple(model_identifiers),
        )
        for provider_id, model_identifiers in sorted(grouped.items())
    )


def _resolve_suite_prompts(
    prompt_repository: InMemoryPromptRepository,
    suite: BenchmarkSuiteConfig,
) -> list[PromptSpec]:
    resolved_prompts = prompt_repository.resolve_prompt_set_ids(
        suite.prompt_set_ids
    )
    seen_prompt_ids = {prompt.prompt_id for prompt in resolved_prompts}
    for prompt_id in suite.prompt_ids:
        if prompt_id in seen_prompt_ids:
            continue
        resolved_prompts.append(prompt_repository.get(prompt_id))
        seen_prompt_ids.add(prompt_id)
    return resolved_prompts


def _normalize_summary_text(text: str) -> str:
    normalized = " ".join(text.split())
    return _TASK_PREFIX_PATTERN.sub("", normalized)
