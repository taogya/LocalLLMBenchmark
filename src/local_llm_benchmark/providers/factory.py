"""task_id 00004-02, 00010-02, 00012-02: provider adapter factory。"""

from __future__ import annotations

from collections.abc import Mapping
import os
from typing import Any

from local_llm_benchmark.config.models import ProviderProfile
from local_llm_benchmark.providers.base import ProviderAdapter
from local_llm_benchmark.providers.openai_compatible.adapter import (
    OpenAICompatibleAdapter,
)
from local_llm_benchmark.providers.openai_compatible.client import (
    OpenAICompatibleClient,
)
from local_llm_benchmark.providers.ollama.adapter import OllamaAdapter
from local_llm_benchmark.providers.ollama.client import OllamaClient


def build_provider_adapters(
    provider_profiles: Mapping[str, ProviderProfile],
) -> dict[str, ProviderAdapter]:
    adapters: dict[str, ProviderAdapter] = {}
    for provider_id, profile in provider_profiles.items():
        adapters[provider_id] = _build_provider_adapter(provider_id, profile)
    return adapters


def _build_provider_adapter(
    provider_id: str,
    profile: ProviderProfile,
) -> ProviderAdapter:
    if provider_id == "ollama":
        return _build_ollama_adapter(provider_id, profile)
    if provider_id == "openai_compatible":
        return _build_openai_compatible_adapter(provider_id, profile)
    raise ValueError(
        f"provider_id '{provider_id}' に対応する adapter factory がありません。"
    )


def _build_ollama_adapter(
    provider_id: str,
    profile: ProviderProfile,
) -> OllamaAdapter:
    base_url = _require_str(profile.connection, "base_url", provider_id)
    timeout_seconds = _optional_float(
        profile.connection.get("timeout_seconds"),
        default=30.0,
        provider_id=provider_id,
    )
    keep_alive = profile.settings.get("keep_alive")
    return OllamaAdapter(
        client=OllamaClient(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        ),
        keep_alive=keep_alive,
        provider_id=provider_id,
    )


def _build_openai_compatible_adapter(
    provider_id: str,
    profile: ProviderProfile,
) -> OpenAICompatibleAdapter:
    base_url = _require_str(profile.connection, "base_url", provider_id)
    timeout_seconds = _optional_float(
        profile.connection.get("timeout_seconds"),
        default=30.0,
        provider_id=provider_id,
    )
    api_key = _resolve_openai_compatible_api_key(
        profile.connection,
        provider_id,
    )
    return OpenAICompatibleAdapter(
        client=OpenAICompatibleClient(
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        ),
        provider_id=provider_id,
    )


def _require_str(
    raw: Mapping[str, Any],
    key: str,
    provider_id: str,
) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"provider_id '{provider_id}' の connection.{key} は "
            "空でない文字列である必要があります。"
        )
    return value


def _optional_float(
    value: object,
    *,
    default: float,
    provider_id: str,
) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise ValueError(
        f"provider_id '{provider_id}' の timeout_seconds は float 互換である必要があります。"
    )


def _optional_str(
    raw: Mapping[str, Any],
    key: str,
    provider_id: str,
) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    raise ValueError(
        f"provider_id '{provider_id}' の connection.{key} は省略するか、"
        "空でない文字列である必要があります。"
    )


def _resolve_openai_compatible_api_key(
    raw: Mapping[str, Any],
    provider_id: str,
) -> str | None:
    if "api_key" in raw:
        raise ValueError(
            f"provider_id '{provider_id}' の connection.api_key は受け付けません。"
            "connection.api_key_env で環境変数名を指定してください。"
        )

    api_key_env = _optional_str(raw, "api_key_env", provider_id)
    if api_key_env is None:
        return None

    api_key = os.environ.get(api_key_env)
    if api_key is None or api_key == "":
        raise ValueError(
            f"provider_id '{provider_id}' の connection.api_key_env が参照する "
            f"環境変数 '{api_key_env}' が未設定または空文字です。"
        )
    return api_key
