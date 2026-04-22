"""task_id 00007-02: suite catalog 表示ロジックの確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.cli.suite_catalog import (
    build_suite_detail_view,
    build_suite_summary_views,
)
from local_llm_benchmark.config.models import (
    AppConfig,
    BenchmarkSuiteConfig,
    ConfigBundle,
    ModelSelector,
    ProviderProfile,
)
from local_llm_benchmark.prompts.models import PromptSet, PromptSpec
from local_llm_benchmark.registry.models import ModelSpec


class SuiteCatalogViewTest(unittest.TestCase):
    def test_build_views_sort_suites_and_group_models_by_provider(
        self,
    ) -> None:
        bundle = ConfigBundle(
            app_config=AppConfig(
                provider_profiles={
                    "provider-b": ProviderProfile(provider_id="provider-b"),
                    "provider-a": ProviderProfile(provider_id="provider-a"),
                },
                benchmark_suites={
                    "suite-z": BenchmarkSuiteConfig(
                        suite_id="suite-z",
                        description="task_id 00007-02: z suite",
                        model_selector=ModelSelector(
                            explicit_model_keys=(
                                "model-b-1",
                                "model-a-1",
                                "model-a-2",
                            )
                        ),
                        prompt_set_ids=("prompt-set-1",),
                        tags=("nightly",),
                    ),
                    "suite-a": BenchmarkSuiteConfig(
                        suite_id="suite-a",
                        description="task_id 00007-02: a suite",
                        model_selector=ModelSelector(
                            explicit_model_keys=("model-a-1",)
                        ),
                        prompt_set_ids=("prompt-set-1",),
                    ),
                },
            ),
            model_specs=(
                ModelSpec(
                    model_key="model-b-1",
                    provider_id="provider-b",
                    provider_model_name="provider-b/model-1",
                ),
                ModelSpec(
                    model_key="model-a-1",
                    provider_id="provider-a",
                    provider_model_name="provider-a/model-1",
                ),
                ModelSpec(
                    model_key="model-a-2",
                    provider_id="provider-a",
                    provider_model_name="provider-a/model-2",
                ),
            ),
            prompt_specs=(
                PromptSpec(
                    prompt_id="prompt-1",
                    version="1",
                    category="rewrite",
                    title="rewrite",
                    description="task_id 00007-02: rewrite",
                    system_message="",
                    user_message="rewrite",
                ),
                PromptSpec(
                    prompt_id="prompt-2",
                    version="1",
                    category="classification",
                    title="classification",
                    description="task_id 00007-02: classification",
                    system_message="",
                    user_message="classify",
                ),
            ),
            prompt_sets=(
                PromptSet(
                    prompt_set_id="prompt-set-1",
                    prompt_ids=("prompt-1", "prompt-2"),
                ),
            ),
        )

        summaries = build_suite_summary_views(bundle)
        detail = build_suite_detail_view(bundle, "suite-z")

        self.assertEqual(
            ["suite-a", "suite-z"],
            [item.suite_id for item in summaries],
        )
        self.assertEqual("z suite", detail.description)
        self.assertEqual(
            ("provider-a", "provider-b"),
            tuple(
                requirement.provider_id
                for requirement in detail.provider_requirements
            ),
        )
        self.assertEqual(
            ("provider-a/model-1", "provider-a/model-2"),
            detail.provider_requirements[0].model_identifiers,
        )
        self.assertEqual(
            ("provider-b/model-1",),
            detail.provider_requirements[1].model_identifiers,
        )
        self.assertEqual(
            ("classification", "rewrite"),
            detail.categories,
        )


if __name__ == "__main__":
    unittest.main()
