"""task_id 00001-03, 00001-08: Ollama chat API へ変換する adapter。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from local_llm_benchmark.benchmark.models import (
    InferenceRequest,
    InferenceResponse,
    InferenceUsage,
)
from local_llm_benchmark.providers.base import ProviderResponseError
from local_llm_benchmark.providers.ollama.client import OllamaClient


@dataclass(slots=True)
class OllamaAdapter:
    client: OllamaClient
    keep_alive: str | int | None = None
    provider_id: str = "ollama"

    def __init__(
        self,
        client: OllamaClient,
        keep_alive: str | int | None = None,
        provider_id: str = "ollama",
    ) -> None:
        self.client = client
        self.keep_alive = keep_alive
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

        raw_response = self.client.chat(
            model_name=request.model.provider_model_name,
            messages=messages,
            generation=request.generation,
            keep_alive=self.keep_alive,
        )
        message = raw_response.get("message")
        if not isinstance(message, dict):
            raise ProviderResponseError("Ollama chat 応答に message がありません。")
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderResponseError(
                "Ollama chat 応答に message.content がありません。"
            )

        prompt_tokens = _optional_int(raw_response.get("prompt_eval_count"))
        completion_tokens = _optional_int(raw_response.get("eval_count"))
        total_tokens = None
        if prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens

        return InferenceResponse(
            output_text=content,
            raw_response=raw_response,
            usage=InferenceUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            latency_ms=_duration_ns_to_ms(raw_response.get("total_duration")),
            finish_reason=_optional_str(raw_response.get("done_reason")),
            provider_metadata={
                "model": raw_response.get("model"),
                "created_at": raw_response.get("created_at"),
                "done": raw_response.get("done"),
                "load_duration_ns": raw_response.get("load_duration"),
            },
        )


def _duration_ns_to_ms(value: object) -> float | None:
    if not isinstance(value, int):
        return None
    return round(value / 1_000_000, 3)


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
