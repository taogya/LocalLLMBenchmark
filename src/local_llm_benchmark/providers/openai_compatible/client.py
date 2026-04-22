"""task_id 00010-02: urllib ベースの最小 OpenAI-compatible client。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib import error, request

from local_llm_benchmark.benchmark.models import GenerationSettings
from local_llm_benchmark.providers.base import (
    ProviderConnectionError,
    ProviderResponseError,
)


@dataclass(slots=True)
class OpenAICompatibleClient:
    base_url: str = "http://localhost:1234/v1"
    timeout_seconds: float = 30.0
    api_key: str | None = None
    user_agent: str = "local-llm-benchmark/0.1.0"

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        timeout_seconds: float = 30.0,
        api_key: str | None = None,
        user_agent: str = "local-llm-benchmark/0.1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.api_key = api_key
        self.user_agent = user_agent

    def chat_completions(
        self,
        *,
        model_name: str,
        messages: Sequence[Mapping[str, Any]],
        generation: GenerationSettings | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [dict(message) for message in messages],
            "stream": False,
        }
        payload.update(
            _generation_to_chat_completions_payload(
                generation or GenerationSettings()
            )
        )
        response = self._request_json(
            "POST",
            "/chat/completions",
            payload,
        )
        if not isinstance(response, dict):
            raise ProviderResponseError(
                "OpenAI-compatible chat completions 応答が JSON object ではありません。"
            )
        return response

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        data = (
            json.dumps(payload).encode("utf-8")
            if payload is not None
            else None
        )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }
        if self.api_key is not None:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        try:
            with request.urlopen(
                req,
                timeout=self.timeout_seconds,
            ) as response:
                raw = response.read()
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ProviderResponseError(
                f"OpenAI-compatible API が HTTP {exc.code} を返しました: {body}"
            ) from exc
        except error.URLError as exc:
            raise ProviderConnectionError(
                f"OpenAI-compatible API に接続できません: {exc.reason}"
            ) from exc

        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(
                "OpenAI-compatible API 応答の JSON 解析に失敗しました。"
            ) from exc


def _generation_to_chat_completions_payload(
    generation: GenerationSettings,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if generation.temperature is not None:
        payload["temperature"] = generation.temperature
    if generation.top_p is not None:
        payload["top_p"] = generation.top_p
    if generation.max_tokens is not None:
        payload["max_tokens"] = generation.max_tokens
    if generation.stop:
        payload["stop"] = list(generation.stop)
    return payload
