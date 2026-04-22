"""task_id 00001-03: OllamaAdapter の正規化確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.benchmark.models import (
    GenerationSettings,
    InferenceRequest,
)
from local_llm_benchmark.prompts.models import EvaluationMetadata, PromptSpec
from local_llm_benchmark.providers.ollama.adapter import OllamaAdapter
from local_llm_benchmark.registry.models import ModelSpec


class FakeOllamaClient:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, *, model_name, messages, generation, keep_alive=None):
        self.calls.append(
            {
                "model_name": model_name,
                "messages": messages,
                "generation": generation,
                "keep_alive": keep_alive,
            }
        )
        return {
            "model": model_name,
            "message": {"content": "接続成功です。"},
            "prompt_eval_count": 12,
            "eval_count": 5,
            "total_duration": 4_500_000,
            "done_reason": "stop",
            "done": True,
        }


class OllamaAdapterTest(unittest.TestCase):
    def test_infer_builds_messages_and_normalizes_response(self) -> None:
        client = FakeOllamaClient()
        adapter = OllamaAdapter(client=client, keep_alive="5m")
        request = InferenceRequest(
            model=ModelSpec(
                model_key="ollama.default",
                provider_id="ollama",
                provider_model_name="gemma3",
            ),
            prompt=PromptSpec(
                prompt_id="prompt-1",
                version="1",
                category="short_qa",
                title="疎通",
                description="task_id 00001-03: adapter test",
                system_message="短く答えてください。",
                user_message="{{keyword}} を含めてください。",
                evaluation_metadata=EvaluationMetadata(
                    primary_metric="manual"
                ),
            ),
            generation=GenerationSettings(temperature=0.0, seed=7),
            prompt_bindings={"keyword": "接続成功"},
            trace_metadata={"task_id": "00001-03"},
        )

        response = adapter.infer(request)

        self.assertEqual("接続成功です。", response.output_text)
        self.assertEqual(4.5, response.latency_ms)
        self.assertEqual("stop", response.finish_reason)
        self.assertEqual(17, response.usage.total_tokens)
        self.assertEqual("system", client.calls[0]["messages"][0]["role"])
        self.assertIn("接続成功", client.calls[0]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
