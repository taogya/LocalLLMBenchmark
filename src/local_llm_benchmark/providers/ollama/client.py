"""task_id 00001-03, 00001-08: urllib ベースの最小 Ollama client。"""

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
class OllamaClient:
    base_url: str = "http://localhost:11434"
    timeout_seconds: float = 30.0
    user_agent: str = "local-llm-benchmark/0.1.0"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 30.0,
        user_agent: str = "local-llm-benchmark/0.1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def get_version(self) -> dict[str, Any]:
        response = self._request_json("GET", "/api/version")
        if not isinstance(response, dict):
            raise ProviderResponseError(
                "Ollama version 応答が JSON object ではありません。"
            )
        return response

    def list_local_models(self) -> dict[str, Any]:
        response = self._request_json("GET", "/api/tags")
        if not isinstance(response, dict):
            raise ProviderResponseError("Ollama tags 応答が JSON object ではありません。")
        return response

    def chat(
        self,
        *,
        model_name: str,
        messages: Sequence[Mapping[str, Any]],
        generation: GenerationSettings | None = None,
        keep_alive: str | int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [dict(message) for message in messages],
            "stream": False,
        }
        options = _generation_to_ollama_options(
            generation or GenerationSettings()
        )
        if options:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        response = self._request_json("POST", "/api/chat", payload)
        if not isinstance(response, dict):
            raise ProviderResponseError("Ollama chat 応答が JSON object ではありません。")
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
        req = request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": self.user_agent,
            },
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
                f"Ollama API が HTTP {exc.code} を返しました: {body}"
            ) from exc
        except error.URLError as exc:
            raise ProviderConnectionError(
                f"Ollama API に接続できません: {exc.reason}"
            ) from exc

        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProviderResponseError(
                "Ollama API 応答の JSON 解析に失敗しました。"
            ) from exc


def _generation_to_ollama_options(
    generation: GenerationSettings,
) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if generation.temperature is not None:
        options["temperature"] = generation.temperature
    if generation.top_p is not None:
        options["top_p"] = generation.top_p
    if generation.max_tokens is not None:
        options["num_predict"] = generation.max_tokens
    if generation.seed is not None:
        options["seed"] = generation.seed
    if generation.stop:
        options["stop"] = list(generation.stop)
    return options
