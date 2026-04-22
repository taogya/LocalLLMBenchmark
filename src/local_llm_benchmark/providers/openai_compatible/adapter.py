"""task_id 00010-02: OpenAI-compatible chat completions へ変換する adapter。"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from local_llm_benchmark.benchmark.models import (
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from local_llm_benchmark.providers.base import ProviderResponseError
from local_llm_benchmark.providers.openai_compatible.client import (
    OpenAICompatibleClient,
)


@dataclass(slots=True)
class OpenAICompatibleAdapter:
    client: OpenAICompatibleClient
    provider_id: str = "openai_compatible"

    def __init__(
        self,
        client: OpenAICompatibleClient,
        provider_id: str = "openai_compatible",
    ) -> None:
        self.client = client
        self.provider_id = provider_id

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        rendered_prompt = request.prompt.render(request.prompt_bindings)
        messages: list[dict[str, Any]] = []
        if rendered_prompt.system_message:
            messages.append(
                {
                    "role": "system",
                    "content": rendered_prompt.system_message,
                }
            )
        messages.append(
            {"role": "user", "content": rendered_prompt.user_message}
        )

        started_at = perf_counter()
        raw_response = self.client.chat_completions(
            model_name=request.model.provider_model_name,
            messages=messages,
            generation=request.generation,
        )
        latency_ms = round((perf_counter() - started_at) * 1000, 3)

        choice = _extract_first_choice(raw_response)
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ProviderResponseError(
                "OpenAI-compatible chat completions 応答に message がありません。"
            )
        content = _extract_message_content(message)

        usage_raw = raw_response.get("usage")
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        if isinstance(usage_raw, dict):
            prompt_tokens = _optional_int(usage_raw.get("prompt_tokens"))
            completion_tokens = _optional_int(
                usage_raw.get("completion_tokens")
            )
            total_tokens = _optional_int(usage_raw.get("total_tokens"))
        if (
            total_tokens is None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = prompt_tokens + completion_tokens

        return InferenceResponse(
            output_text=content,
            raw_response=raw_response,
            usage=InferenceUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            latency_ms=latency_ms,
            finish_reason=_optional_str(choice.get("finish_reason")),
            provider_metadata={
                "id": raw_response.get("id"),
                "created": raw_response.get("created"),
                "model": raw_response.get("model"),
                "system_fingerprint": raw_response.get(
                    "system_fingerprint"
                ),
                "choice_index": choice.get("index"),
                "role": message.get("role"),
            },
        )


def _extract_first_choice(raw_response: dict[str, Any]) -> dict[str, Any]:
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderResponseError(
            "OpenAI-compatible chat completions 応答に choices がありません。"
        )
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ProviderResponseError(
            "OpenAI-compatible chat completions 応答の"
            " choices[0] が object ではありません。"
        )
    return choice


def _extract_message_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
        if parts:
            return "".join(parts)
    raise ProviderResponseError(
        "OpenAI-compatible chat completions 応答に message.content がありません。"
    )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
