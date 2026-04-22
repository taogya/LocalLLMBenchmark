"""task_id 00001-03: PromptRepository の解決確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.prompts.models import (
    EvaluationMetadata,
    PromptSet,
    PromptSpec,
)
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository


class PromptRepositoryTest(unittest.TestCase):
    def test_resolve_prompt_set_ids_uses_only_direct_ids_without_filters(
        self,
    ) -> None:
        prompt_a = PromptSpec(
            prompt_id="prompt-a",
            version="1",
            category="classification",
            title="A",
            description="task_id 00001-04: prompt A",
            system_message="",
            user_message="A",
            evaluation_metadata=EvaluationMetadata(primary_metric="manual"),
        )
        prompt_b = PromptSpec(
            prompt_id="prompt-b",
            version="1",
            category="short_qa",
            title="B",
            description="task_id 00001-04: prompt B",
            system_message="",
            user_message="B",
            evaluation_metadata=EvaluationMetadata(primary_metric="manual"),
        )
        repository = InMemoryPromptRepository(
            [prompt_a, prompt_b],
            [
                PromptSet(
                    prompt_set_id="set-1",
                    prompt_ids=("prompt-a",),
                )
            ],
        )

        resolved = repository.resolve_prompt_set_ids(("set-1",))

        self.assertEqual(
            ["prompt-a"],
            [prompt.prompt_id for prompt in resolved],
        )

    def test_resolve_prompt_set_ids_uses_direct_ids_and_tags(self) -> None:
        prompt_a = PromptSpec(
            prompt_id="prompt-a",
            version="1",
            category="classification",
            title="A",
            description="task_id 00001-03: prompt A",
            system_message="",
            user_message="A",
            tags=("smoke",),
            evaluation_metadata=EvaluationMetadata(primary_metric="manual"),
        )
        prompt_b = PromptSpec(
            prompt_id="prompt-b",
            version="1",
            category="short_qa",
            title="B",
            description="task_id 00001-03: prompt B",
            system_message="",
            user_message="B",
            tags=("smoke", "ja"),
            evaluation_metadata=EvaluationMetadata(primary_metric="manual"),
        )
        repository = InMemoryPromptRepository(
            [prompt_a, prompt_b],
            [
                PromptSet(
                    prompt_set_id="set-1",
                    prompt_ids=("prompt-a",),
                    include_tags=("smoke",),
                )
            ],
        )

        resolved = repository.resolve_prompt_set_ids(("set-1",))

        self.assertEqual(
            ["prompt-a", "prompt-b"],
            [prompt.prompt_id for prompt in resolved],
        )


if __name__ == "__main__":
    unittest.main()
