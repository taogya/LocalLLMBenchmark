"""task_id 00001-03, 00004-02: 外部 TOML 設定を読み込む loader。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tomllib
from typing import Any, Mapping

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    GenerationSettings,
)
from local_llm_benchmark.config.models import (
    AppConfig,
    BenchmarkSuiteConfig,
    ConfigBundle,
    ModelSelector,
    ProviderProfile,
)
from local_llm_benchmark.prompts.models import (
    EvaluationMetadata,
    PromptSet,
    PromptSpec,
    PromptVariable,
)
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry
from local_llm_benchmark.registry.models import ModelSpec


@dataclass(slots=True)
class ConfigLayout:
    benchmark_suites_dir: Path
    model_registry_dir: Path
    prompt_sets_dir: Path
    provider_profiles_dir: Path
    prompts_dir: Path


def load_config_bundle(config_root: str | Path) -> ConfigBundle:
    layout = _resolve_config_layout(config_root)
    provider_profiles = _load_provider_profiles(layout.provider_profiles_dir)
    model_specs = _load_model_specs(layout.model_registry_dir)
    prompt_specs = _load_prompt_specs(layout.prompts_dir)
    prompt_sets = _load_prompt_sets(layout.prompt_sets_dir)
    benchmark_suites = _load_benchmark_suites(layout.benchmark_suites_dir)

    bundle = ConfigBundle(
        app_config=AppConfig(
            provider_profiles=provider_profiles,
            benchmark_suites=benchmark_suites,
        ),
        model_specs=tuple(model_specs),
        prompt_specs=tuple(prompt_specs),
        prompt_sets=tuple(prompt_sets),
    )
    _validate_bundle(bundle)
    return bundle


def build_benchmark_plan(
    bundle: ConfigBundle,
    *,
    suite_id: str,
    run_id: str | None = None,
    trace_metadata: Mapping[str, Any] | None = None,
) -> BenchmarkPlan:
    try:
        suite = bundle.app_config.benchmark_suites[suite_id]
    except KeyError as exc:
        raise KeyError(
            f"suite_id '{suite_id}' は config bundle に存在しません。"
        ) from exc

    metadata = {
        "task_id": "00004-02",
        "config_source": "external_toml",
    }
    if trace_metadata is not None:
        metadata.update(dict(trace_metadata))

    return BenchmarkPlan(
        run_id=run_id or _default_run_id(suite_id),
        suite_id=suite.suite_id,
        model_selector=suite.model_selector,
        prompt_set_ids=suite.prompt_set_ids,
        prompt_ids=suite.prompt_ids,
        default_generation=suite.generation_overrides,
        trace_metadata=metadata,
    )


def _resolve_config_layout(config_root: str | Path) -> ConfigLayout:
    requested_root = Path(config_root).expanduser().resolve()
    config_base = _resolve_config_base(requested_root)
    prompts_dir = _resolve_prompts_dir(requested_root, config_base)
    return ConfigLayout(
        benchmark_suites_dir=config_base / "benchmark_suites",
        model_registry_dir=config_base / "model_registry",
        prompt_sets_dir=config_base / "prompt_sets",
        provider_profiles_dir=config_base / "provider_profiles",
        prompts_dir=prompts_dir,
    )


def _resolve_config_base(requested_root: Path) -> Path:
    if _has_config_directories(requested_root):
        return requested_root

    candidate = requested_root / "configs"
    if _has_config_directories(candidate):
        return candidate

    raise FileNotFoundError(
        "config root から benchmark_suites、model_registry、prompt_sets、"
        "provider_profiles を見つけられませんでした。"
    )


def _resolve_prompts_dir(requested_root: Path, config_base: Path) -> Path:
    candidates: list[Path] = []
    for candidate in (
        config_base / "prompts",
        config_base.parent / "prompts",
        requested_root / "prompts",
    ):
        if candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        "config root に対応する prompts ディレクトリを見つけられませんでした。"
    )


def _has_config_directories(base_dir: Path) -> bool:
    required = (
        "benchmark_suites",
        "model_registry",
        "prompt_sets",
        "provider_profiles",
    )
    return base_dir.is_dir() and all(
        (base_dir / name).is_dir() for name in required
    )


def _load_provider_profiles(
    directory: Path,
) -> dict[str, ProviderProfile]:
    seen_provider_ids: dict[str, Path] = {}
    profiles: dict[str, ProviderProfile] = {}
    for file_path in _iter_toml_files(directory):
        raw = _read_toml_file(file_path)
        provider_id = _require_str(raw, "provider_id", file_path)
        _register_unique(
            seen_provider_ids,
            provider_id,
            file_path,
            "provider_id",
        )
        profiles[provider_id] = ProviderProfile(
            provider_id=provider_id,
            connection=_optional_mapping(raw.get("connection")),
            settings=_optional_mapping(raw.get("settings")),
            metadata=_optional_mapping(raw.get("metadata")),
        )
    return profiles


def _load_model_specs(directory: Path) -> list[ModelSpec]:
    model_specs: list[ModelSpec] = []
    seen_model_keys: dict[str, Path] = {}
    for file_path in _iter_toml_files(directory):
        raw = _read_toml_file(file_path)
        records = raw.get("models")
        if records is None:
            records = [raw]
        if not isinstance(records, list):
            raise ValueError(
                f"{file_path} の models は配列である必要があります。"
            )
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(
                    f"{file_path} の model record は table である必要があります。"
                )
            model_key = _require_str(record, "model_key", file_path)
            _register_unique(
                seen_model_keys,
                model_key,
                file_path,
                "model_key",
            )
            model_specs.append(
                ModelSpec(
                    model_key=model_key,
                    provider_id=_require_str(record, "provider_id", file_path),
                    provider_model_name=_require_str(
                        record,
                        "provider_model_name",
                        file_path,
                    ),
                    capability_tags=_as_string_tuple(
                        record.get("capability_tags", []),
                        file_path,
                        "capability_tags",
                    ),
                    default_generation=_parse_generation_settings(
                        _optional_mapping(record.get("default_generation")),
                        file_path,
                    ),
                    metadata=_optional_mapping(record.get("metadata")),
                )
            )
    return model_specs


def _load_prompt_specs(directory: Path) -> list[PromptSpec]:
    prompt_specs: list[PromptSpec] = []
    seen_prompt_ids: dict[str, Path] = {}
    for file_path in sorted(directory.rglob("*.toml")):
        raw = _read_toml_file(file_path)
        prompt_id = _require_str(raw, "prompt_id", file_path)
        _register_unique(seen_prompt_ids, prompt_id, file_path, "prompt_id")
        variables = raw.get("variables", [])
        if not isinstance(variables, list):
            raise ValueError(
                f"{file_path} の variables は配列である必要があります。"
            )
        prompt_specs.append(
            PromptSpec(
                prompt_id=prompt_id,
                version=_require_str(raw, "version", file_path),
                category=_require_str(raw, "category", file_path),
                title=_require_str(raw, "title", file_path),
                description=_require_str(raw, "description", file_path),
                system_message=_require_text(
                    raw,
                    "system_message",
                    file_path,
                ),
                user_message=_require_str(raw, "user_message", file_path),
                variables=tuple(
                    _parse_prompt_variable(variable, file_path)
                    for variable in variables
                ),
                recommended_generation=_parse_generation_settings(
                    _optional_mapping(raw.get("recommended_generation")),
                    file_path,
                ),
                tags=_as_string_tuple(raw.get("tags", []), file_path, "tags"),
                evaluation_metadata=_parse_evaluation_metadata(
                    _optional_mapping(raw.get("evaluation_metadata")),
                    file_path,
                ),
                output_contract=_optional_mapping(raw.get("output_contract")),
                metadata=_optional_mapping(raw.get("metadata")),
            )
        )
    return prompt_specs


def _load_prompt_sets(directory: Path) -> list[PromptSet]:
    prompt_sets: list[PromptSet] = []
    seen_prompt_set_ids: dict[str, Path] = {}
    for file_path in _iter_toml_files(directory):
        raw = _read_toml_file(file_path)
        prompt_set_id = _require_str(raw, "prompt_set_id", file_path)
        _register_unique(
            seen_prompt_set_ids,
            prompt_set_id,
            file_path,
            "prompt_set_id",
        )
        prompt_sets.append(
            PromptSet(
                prompt_set_id=prompt_set_id,
                description=_optional_str(raw.get("description")) or "",
                prompt_ids=_as_string_tuple(
                    raw.get("prompt_ids", []),
                    file_path,
                    "prompt_ids",
                ),
                include_categories=_as_string_tuple(
                    raw.get("include_categories", []),
                    file_path,
                    "include_categories",
                ),
                include_tags=_as_string_tuple(
                    raw.get("include_tags", []),
                    file_path,
                    "include_tags",
                ),
            )
        )
    return prompt_sets


def _load_benchmark_suites(
    directory: Path,
) -> dict[str, BenchmarkSuiteConfig]:
    seen_suite_ids: dict[str, Path] = {}
    benchmark_suites: dict[str, BenchmarkSuiteConfig] = {}
    for file_path in _iter_toml_files(directory):
        raw = _read_toml_file(file_path)
        suite_id = _require_str(raw, "suite_id", file_path)
        _register_unique(seen_suite_ids, suite_id, file_path, "suite_id")
        model_selector_raw = _optional_mapping(raw.get("model_selector"))
        benchmark_suites[suite_id] = BenchmarkSuiteConfig(
            suite_id=suite_id,
            description=_require_str(raw, "description", file_path),
            model_selector=ModelSelector(
                explicit_model_keys=_as_string_tuple(
                    model_selector_raw.get("explicit_model_keys", []),
                    file_path,
                    "model_selector.explicit_model_keys",
                ),
                include_tags=_as_string_tuple(
                    model_selector_raw.get("include_tags", []),
                    file_path,
                    "model_selector.include_tags",
                ),
                provider_id=_optional_str(
                    model_selector_raw.get("provider_id")
                ),
            ),
            prompt_set_ids=_as_string_tuple(
                raw.get("prompt_set_ids", []),
                file_path,
                "prompt_set_ids",
            ),
            prompt_ids=_as_string_tuple(
                raw.get("prompt_ids", []),
                file_path,
                "prompt_ids",
            ),
            generation_overrides=_parse_generation_settings(
                _optional_mapping(raw.get("generation_overrides")),
                file_path,
            ),
            tags=_as_string_tuple(raw.get("tags", []), file_path, "tags"),
            metadata=_optional_mapping(raw.get("metadata")),
        )
    return benchmark_suites


def _validate_bundle(bundle: ConfigBundle) -> None:
    provider_profiles = bundle.app_config.provider_profiles
    prompt_ids = {prompt.prompt_id for prompt in bundle.prompt_specs}
    model_specs_by_key = {
        model.model_key: model for model in bundle.model_specs
    }
    prompt_sets_by_id = {
        prompt_set.prompt_set_id: prompt_set
        for prompt_set in bundle.prompt_sets
    }

    for model in bundle.model_specs:
        if model.provider_id not in provider_profiles:
            raise ValueError(
                f"model_key '{model.model_key}' が未定義の provider_id "
                f"'{model.provider_id}' を参照しています。"
            )

    for prompt_set in bundle.prompt_sets:
        if not (
            prompt_set.prompt_ids
            or prompt_set.include_categories
            or prompt_set.include_tags
        ):
            raise ValueError(
                f"prompt_set_id '{prompt_set.prompt_set_id}' に解決条件がありません。"
            )
        missing_prompt_ids = [
            prompt_id
            for prompt_id in prompt_set.prompt_ids
            if prompt_id not in prompt_ids
        ]
        if missing_prompt_ids:
            joined = ", ".join(missing_prompt_ids)
            raise ValueError(
                f"prompt_set_id '{prompt_set.prompt_set_id}' が未定義の "
                f"prompt_id を参照しています: {joined}"
            )

    model_registry = InMemoryModelRegistry(list(bundle.model_specs))
    prompt_repository = InMemoryPromptRepository(
        list(bundle.prompt_specs),
        list(bundle.prompt_sets),
    )
    for suite in bundle.app_config.benchmark_suites.values():
        if suite.model_selector.provider_id is not None and (
            suite.model_selector.provider_id not in provider_profiles
        ):
            raise ValueError(
                f"suite_id '{suite.suite_id}' が未定義の provider_id "
                f"'{suite.model_selector.provider_id}' を参照しています。"
            )

        missing_prompt_set_ids = [
            prompt_set_id
            for prompt_set_id in suite.prompt_set_ids
            if prompt_set_id not in prompt_sets_by_id
        ]
        if missing_prompt_set_ids:
            joined = ", ".join(missing_prompt_set_ids)
            raise ValueError(
                f"suite_id '{suite.suite_id}' が未定義の prompt_set_id を "
                f"参照しています: {joined}"
            )

        missing_prompt_ids = [
            prompt_id
            for prompt_id in suite.prompt_ids
            if prompt_id not in prompt_ids
        ]
        if missing_prompt_ids:
            joined = ", ".join(missing_prompt_ids)
            raise ValueError(
                f"suite_id '{suite.suite_id}' が未定義の prompt_id を参照しています: "
                f"{joined}"
            )

        missing_model_keys = [
            model_key
            for model_key in suite.model_selector.explicit_model_keys
            if model_key not in model_specs_by_key
        ]
        if missing_model_keys:
            joined = ", ".join(missing_model_keys)
            raise ValueError(
                f"suite_id '{suite.suite_id}' が未定義の model_key を参照しています: "
                f"{joined}"
            )

        if suite.model_selector.provider_id is not None:
            for model_key in suite.model_selector.explicit_model_keys:
                model = model_specs_by_key[model_key]
                if model.provider_id != suite.model_selector.provider_id:
                    raise ValueError(
                        f"suite_id '{suite.suite_id}' の model_key "
                        f"'{model_key}' は provider_id "
                        f"'{suite.model_selector.provider_id}' と"
                        "一致しません。"
                    )

        resolved_models = model_registry.resolve_selector(suite.model_selector)
        if not resolved_models:
            raise ValueError(
                f"suite_id '{suite.suite_id}' からモデルを解決できませんでした。"
            )

        resolved_prompts = prompt_repository.resolve_prompt_set_ids(
            suite.prompt_set_ids
        )
        seen_prompt_ids = {prompt.prompt_id for prompt in resolved_prompts}
        for prompt_id in suite.prompt_ids:
            if prompt_id in seen_prompt_ids:
                continue
            resolved_prompts.append(prompt_repository.get(prompt_id))
            seen_prompt_ids.add(prompt_id)
        if not resolved_prompts:
            raise ValueError(
                f"suite_id '{suite.suite_id}' からプロンプトを解決できませんでした。"
            )


def _iter_toml_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.glob("*.toml") if path.is_file())


def _read_toml_file(file_path: Path) -> dict[str, Any]:
    with file_path.open("rb") as stream:
        raw = tomllib.load(stream)
    if not isinstance(raw, dict):
        raise ValueError(f"{file_path} の TOML ルートは table である必要があります。")
    return raw


def _parse_prompt_variable(
    raw: dict[str, Any],
    file_path: Path,
) -> PromptVariable:
    return PromptVariable(
        name=_require_str(raw, "name", file_path),
        type=_require_str(raw, "type", file_path),
        required=_optional_bool(raw.get("required"), default=True),
        description=_optional_str(raw.get("description")) or "",
        default=raw.get("default"),
        example=raw.get("example"),
        validation=_optional_mapping(raw.get("validation")),
    )


def _parse_evaluation_metadata(
    raw: dict[str, Any],
    file_path: Path,
) -> EvaluationMetadata:
    if not raw:
        return EvaluationMetadata(primary_metric="exact_match")
    return EvaluationMetadata(
        primary_metric=_require_str(raw, "primary_metric", file_path),
        secondary_metrics=_as_string_tuple(
            raw.get("secondary_metrics", []),
            file_path,
            "evaluation_metadata.secondary_metrics",
        ),
        reference_type=_optional_str(raw.get("reference_type")) or "text",
        scorer=_optional_str(raw.get("scorer")) or "exact_match",
        difficulty=_optional_str(raw.get("difficulty")) or "starter",
        language=_optional_str(raw.get("language")) or "ja",
        expected_output_format=(
            _optional_str(raw.get("expected_output_format")) or "text"
        ),
    )


def _parse_generation_settings(
    raw: dict[str, Any],
    file_path: Path,
) -> GenerationSettings:
    max_output_tokens = raw.get("max_output_tokens", raw.get("max_tokens"))
    return GenerationSettings(
        temperature=_optional_float(raw.get("temperature"), file_path),
        top_p=_optional_float(raw.get("top_p"), file_path),
        max_tokens=_optional_int(max_output_tokens, file_path),
        seed=_optional_int(raw.get("seed"), file_path),
        stop=_as_string_tuple(raw.get("stop", []), file_path, "stop"),
    )


def _register_unique(
    registry: dict[str, Path],
    key: str,
    file_path: Path,
    label: str,
) -> None:
    if key in registry:
        previous_path = registry[key]
        raise ValueError(
            f"{label} '{key}' が重複しています: {previous_path} / {file_path}"
        )
    registry[key] = file_path


def _require_str(raw: Mapping[str, Any], key: str, file_path: Path) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{file_path} の '{key}' は空でない文字列である必要があります。")
    return value


def _require_text(raw: Mapping[str, Any], key: str, file_path: Path) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{file_path} の '{key}' は文字列である必要があります。")
    return value


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("table である必要がある値が見つかりました。")
    return dict(value)


def _optional_bool(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError("bool である必要がある値が見つかりました。")
    return value


def _optional_float(value: object, file_path: Path) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise ValueError(f"{file_path} の数値項目は float 互換である必要があります。")


def _optional_int(value: object, file_path: Path) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError(f"{file_path} の整数項目は int である必要があります。")


def _as_string_tuple(
    value: object,
    file_path: Path,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{file_path} の '{field_name}' は配列である必要があります。")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(
                f"{file_path} の '{field_name}' は空でない文字列配列である必要があります。"
            )
        items.append(item)
    return tuple(items)


def _default_run_id(suite_id: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    normalized_suite_id = "-".join(part for part in suite_id.split() if part)
    return f"{normalized_suite_id}-{timestamp}"
