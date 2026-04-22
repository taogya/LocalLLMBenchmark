"""task_id 00010-02: OpenAICompatibleAdapter の正規化確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.benchmark.models import (
    GenerationSettings,
    InferenceRequest,
)
from local_llm_benchmark.prompts.models import EvaluationMetadata, PromptSpec
from local_llm_benchmark.providers.base import ProviderResponseError
from local_llm_benchmark.providers.openai_compatible.adapter import (
    OpenAICompatibleAdapter,
)
from local_llm_benchmark.registry.models import ModelSpec


class FakeOpenAICompatibleClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls = []

    def chat_completions(self, *, model_name, messages, generation):
        self.calls.append(
            {
                "model_name": model_name,
                "messages": messages,
                "generation": generation,
            }
        )
        return dict(self.response)


class OpenAICompatibleAdapterTest(unittest.TestCase):
    def test_infer_builds_messages_and_normalizes_response(self) -> None:
        client = FakeOpenAICompatibleClient(
            {
                "id": "chatcmpl-local-1",
                "created": 1710000000,
                "model": "local-model",
                "system_fingerprint": "fp-local",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "接続成功です。",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 5,
                    "total_tokens": 17,
                },
            }
        )
        adapter = OpenAICompatibleAdapter(client=client)
        request = InferenceRequest(
            model=ModelSpec(
                model_key="openai_compatible.default",
                provider_id="openai_compatible",
                provider_model_name="local-model",
            ),
            prompt=PromptSpec(
                prompt_id="prompt-1",
                version="1",
                category="short_qa",
                title="疎通",
                description="task_id 00010-02: adapter test",
                system_message="短く答えてください。",
                user_message="{{keyword}} を含めてください。",
                evaluation_metadata=EvaluationMetadata(
                    primary_metric="manual"
                ),
            ),
            generation=GenerationSettings(
                temperature=0.0,
                top_p=0.95,
                max_tokens=64,
                seed=7,
            ),
            prompt_bindings={"keyword": "接続成功"},
            trace_metadata={"task_id": "00010-02"},
        )

        response = adapter.infer(request)

        self.assertEqual("接続成功です。", response.output_text)
        self.assertEqual("stop", response.finish_reason)
        self.assertEqual(17, response.usage.total_tokens)
        self.assertIsNotNone(response.latency_ms)
        self.assertEqual("chatcmpl-local-1", response.provider_metadata["id"])
        self.assertEqual("assistant", response.provider_metadata["role"])
        self.assertEqual("system", client.calls[0]["messages"][0]["role"])
        self.assertIn("接続成功", client.calls[0]["messages"][1]["content"])
        self.assertEqual("local-model", client.calls[0]["model_name"])

    def test_infer_raises_when_message_content_is_missing(self) -> None:
        client = FakeOpenAICompatibleClient(
            {
                "choices": [{"message": {}, "finish_reason": "stop"}],
            }
        )
        adapter = OpenAICompatibleAdapter(client=client)
        request = InferenceRequest(
            model=ModelSpec(
                model_key="openai_compatible.default",
                provider_id="openai_compatible",
                provider_model_name="local-model",
            ),
            prompt=PromptSpec(
                prompt_id="prompt-1",
                version="1",
                category="short_qa",
                title="疎通",
                description="task_id 00010-02: adapter test",
                system_message="",
                user_message="返答してください。",
                evaluation_metadata=EvaluationMetadata(
                    primary_metric="manual"
                ),
            ),
            generation=GenerationSettings(),
        )

        with self.assertRaisesRegex(
            ProviderResponseError,
            "message.content がありません",
        ):
            adapter.infer(request)


if __name__ == "__main__":
    unittest.main()
