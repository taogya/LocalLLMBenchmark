"""task_id 00004-02, 00009-04, 00012-02, 00016-02: 外部 TOML 設定 loader の確認。"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from local_llm_benchmark.config.loader import load_config_bundle
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"


class ConfigLoaderTest(unittest.TestCase):
    def test_load_config_bundle_resolves_three_tier_suite(self) -> None:
        bundle = load_config_bundle(CONFIG_ROOT)
        self.assertIn("ollama", bundle.app_config.provider_profiles)
        self.assertIn(
            "openai_compatible",
            bundle.app_config.provider_profiles,
        )
        self.assertEqual(
            "http://localhost:1234/v1",
            bundle.app_config.provider_profiles[
                "openai_compatible"
            ].connection["base_url"],
        )
        self.assertEqual(
            30.0,
            bundle.app_config.provider_profiles[
                "openai_compatible"
            ].connection["timeout_seconds"],
        )
        self.assertNotIn(
            "api_key",
            bundle.app_config.provider_profiles[
                "openai_compatible"
            ].connection,
        )
        suite = bundle.app_config.benchmark_suites[
            "local-three-tier-baseline-v1"
        ]

        registry = InMemoryModelRegistry(list(bundle.model_specs))
        resolved_models = registry.resolve_selector(suite.model_selector)
        self.assertEqual(
            [
                "local.entry.gemma3",
                "local.balanced.qwen2_5",
                "local.quality.llama3_1",
            ],
            [model.model_key for model in resolved_models],
        )
        self.assertEqual(
            ["tier:entry", "tier:balanced", "tier:quality"],
            [
                next(
                    tag
                    for tag in model.capability_tags
                    if tag.startswith("tier:")
                )
                for model in resolved_models
            ],
        )

        repository = InMemoryPromptRepository(
            list(bundle.prompt_specs),
            list(bundle.prompt_sets),
        )
        resolved_prompts = repository.resolve_prompt_set_ids(
            suite.prompt_set_ids
        )
        self.assertEqual(
            [
                "contact-routing-v1",
                "invoice-fields-v1",
                "polite-rewrite-v1",
                "meeting-notice-summary-v1",
                "support-hours-answer-v1",
                "followup-action-json-v1",
            ],
            [prompt.prompt_id for prompt in resolved_prompts],
        )
        prompt_by_id = {
            prompt.prompt_id: prompt for prompt in resolved_prompts
        }
        self.assertEqual(
            {},
            prompt_by_id["polite-rewrite-v1"].metadata["evaluation_reference"],
        )
        self.assertEqual(
            "17:00",
            prompt_by_id["support-hours-answer-v1"].metadata[
                "evaluation_reference"
            ]["text"],
        )

    def test_load_config_bundle_resolves_openai_compatible_readiness_suite(
        self,
    ) -> None:
        bundle = load_config_bundle(CONFIG_ROOT)
        suite = bundle.app_config.benchmark_suites[
            "openai-compatible-minimal-v1"
        ]

        registry = InMemoryModelRegistry(list(bundle.model_specs))
        resolved_models = registry.resolve_selector(suite.model_selector)
        self.assertEqual(
            ["local.openai_compatible.readiness"],
            [model.model_key for model in resolved_models],
        )
        self.assertEqual(
            ["openai_compatible"],
            [model.provider_id for model in resolved_models],
        )
        self.assertEqual(
            ["llmb-minimal-chat"],
            [model.provider_model_name for model in resolved_models],
        )

        repository = InMemoryPromptRepository(
            list(bundle.prompt_specs),
            list(bundle.prompt_sets),
        )
        resolved_prompts = repository.resolve_prompt_set_ids(
            suite.prompt_set_ids
        )
        self.assertEqual(
            [
                "contact-routing-v1",
                "invoice-fields-v1",
                "support-hours-answer-v1",
            ],
            [prompt.prompt_id for prompt in resolved_prompts],
        )

    def test_load_config_bundle_rejects_unknown_provider_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            config_root = base_dir / "configs"
            prompts_root = base_dir / "prompts"

            for subdir in (
                config_root / "benchmark_suites",
                config_root / "model_registry",
                config_root / "prompt_sets",
                config_root / "provider_profiles",
                prompts_root / "classification",
            ):
                subdir.mkdir(parents=True, exist_ok=True)

            (
                config_root / "provider_profiles" / "local-default.toml"
            ).write_text(
                """
provider_id = "provider-a"

[connection]
base_url = "http://localhost:11434"
timeout_seconds = 30.0
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (config_root / "model_registry" / "models.toml").write_text(
                """
[[models]]
model_key = "local.invalid"
provider_id = "provider-b"
provider_model_name = "model-a"
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (config_root / "prompt_sets" / "set.toml").write_text(
                """
prompt_set_id = "set-1"
description = "task_id 00004-02: invalid provider reference"
prompt_ids = ["prompt-1"]
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (config_root / "benchmark_suites" / "suite.toml").write_text(
                """
suite_id = "suite-1"
description = "task_id 00004-02: invalid provider reference"
prompt_set_ids = ["set-1"]

[model_selector]
explicit_model_keys = ["local.invalid"]
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (prompts_root / "classification" / "prompt-1.toml").write_text(
                """
prompt_id = "prompt-1"
version = "1"
category = "classification"
title = "invalid"
description = "task_id 00004-02: invalid provider reference"
system_message = ""
user_message = "test"

[evaluation_metadata]
primary_metric = "manual"
""".strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "未定義の provider_id"):
                load_config_bundle(config_root)

    def test_load_config_bundle_reports_duplicate_provider_profile_paths(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            config_root = base_dir / "configs"
            prompts_root = base_dir / "prompts"

            for subdir in (
                config_root / "benchmark_suites",
                config_root / "model_registry",
                config_root / "prompt_sets",
                config_root / "provider_profiles",
                prompts_root / "classification",
            ):
                subdir.mkdir(parents=True, exist_ok=True)

            for file_name in ("first.toml", "second.toml"):
                (
                    config_root / "provider_profiles" / file_name
                ).write_text(
                    """
provider_id = "provider-a"

[connection]
base_url = "http://localhost:11434"
""".strip()
                    + "\n",
                    encoding="utf-8",
                )

            with self.assertRaises(ValueError) as context:
                load_config_bundle(config_root)

            message = str(context.exception)
            self.assertIn("provider_id 'provider-a' が重複しています", message)
            self.assertIn("first.toml", message)
            self.assertIn("second.toml", message)
