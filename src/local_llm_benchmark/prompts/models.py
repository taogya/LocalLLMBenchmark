"""task_id 00001-03: provider 非依存の prompt dataclass。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from local_llm_benchmark.benchmark.models import GenerationSettings

_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


@dataclass(slots=True)
class PromptVariable:
    name: str
    type: Literal["string", "integer", "float", "boolean", "string_list"]
    required: bool = True
    description: str = ""
    default: Any | None = None
    example: Any | None = None
    validation: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvaluationMetadata:
    primary_metric: str
    secondary_metrics: tuple[str, ...] = ()
    reference_type: Literal["label", "text", "json", "none"] = "text"
    scorer: str = "exact_match"
    difficulty: Literal["starter", "standard", "advanced"] = "starter"
    language: str = "ja"
    expected_output_format: Literal["text", "json", "bullet_list"] = "text"


@dataclass(slots=True)
class RenderedPrompt:
    system_message: str
    user_message: str


@dataclass(slots=True)
class PromptSpec:
    prompt_id: str
    version: str
    category: str
    title: str
    description: str
    system_message: str
    user_message: str
    variables: tuple[PromptVariable, ...] = ()
    recommended_generation: GenerationSettings = field(
        default_factory=GenerationSettings
    )
    tags: tuple[str, ...] = ()
    evaluation_metadata: EvaluationMetadata = field(
        default_factory=lambda: EvaluationMetadata(
            primary_metric="exact_match"
        )
    )
    output_contract: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(
        self,
        bindings: Mapping[str, Any] | None = None,
    ) -> RenderedPrompt:
        resolved_bindings = dict(bindings or {})
        for variable in self.variables:
            if (
                variable.name not in resolved_bindings
                and variable.default is not None
            ):
                resolved_bindings[variable.name] = variable.default
        missing = [
            variable.name
            for variable in self.variables
            if variable.required and variable.name not in resolved_bindings
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(
                f"prompt '{self.prompt_id}' に必要な変数が不足しています: "
                f"{joined}"
            )
        return RenderedPrompt(
            system_message=_render_template(
                self.system_message,
                resolved_bindings,
            ),
            user_message=_render_template(
                self.user_message,
                resolved_bindings,
            ),
        )


@dataclass(slots=True)
class PromptSet:
    prompt_set_id: str
    description: str = ""
    prompt_ids: tuple[str, ...] = ()
    include_categories: tuple[str, ...] = ()
    include_tags: tuple[str, ...] = ()


def _render_template(template: str, bindings: Mapping[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in bindings:
            return match.group(0)
        value = bindings[key]
        if isinstance(value, (list, tuple)):
            return ", ".join(str(item) for item in value)
        return str(value)

    return _PLACEHOLDER_PATTERN.sub(replace, template)
