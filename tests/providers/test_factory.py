"""task_id 00010-02, 00012-02: provider factory の dispatch 確認。"""

from __future__ import annotations

import unittest
from unittest import mock

from local_llm_benchmark.config.models import ProviderProfile
from local_llm_benchmark.providers.factory import build_provider_adapters
from local_llm_benchmark.providers.openai_compatible.adapter import (
    OpenAICompatibleAdapter,
)
from local_llm_benchmark.providers.ollama.adapter import OllamaAdapter


class ProviderFactoryTest(unittest.TestCase):
    def test_build_provider_adapters_supports_ollama_and_keyless_openai(
        self,
    ) -> None:
        adapters = build_provider_adapters(
            {
                "ollama": ProviderProfile(
                    provider_id="ollama",
                    connection={
                        "base_url": "http://localhost:11434",
                        "timeout_seconds": 30.0,
                    },
                    settings={"keep_alive": "5m"},
                ),
                "openai_compatible": ProviderProfile(
                    provider_id="openai_compatible",
                    connection={
                        "base_url": "http://localhost:1234/v1",
                        "timeout_seconds": 15.0,
                    },
                ),
            }
        )

        self.assertIsInstance(adapters["ollama"], OllamaAdapter)
        self.assertIsInstance(
            adapters["openai_compatible"],
            OpenAICompatibleAdapter,
        )
        self.assertEqual(
            "http://localhost:1234/v1",
            adapters["openai_compatible"].client.base_url,
        )
        self.assertIsNone(adapters["openai_compatible"].client.api_key)

    def test_build_provider_adapters_resolves_openai_compatible_api_key_env(
        self,
    ) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY": "local-secret"
            },
            clear=False,
        ):
            adapters = build_provider_adapters(
                {
                    "openai_compatible": ProviderProfile(
                        provider_id="openai_compatible",
                        connection={
                            "base_url": "http://localhost:1234/v1",
                            "api_key_env": (
                                "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY"
                            ),
                        },
                    )
                }
            )

        self.assertEqual(
            "local-secret",
            adapters["openai_compatible"].client.api_key,
        )

    def test_build_provider_adapters_rejects_invalid_openai_compatible_profile(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "connection.base_url"):
            build_provider_adapters(
                {
                    "openai_compatible": ProviderProfile(
                        provider_id="openai_compatible",
                        connection={},
                    )
                }
            )

    def test_build_provider_adapters_rejects_missing_api_key_env(
        self,
    ) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "未設定または空文字",
            ):
                build_provider_adapters(
                    {
                        "openai_compatible": ProviderProfile(
                            provider_id="openai_compatible",
                            connection={
                                "base_url": "http://localhost:1234/v1",
                                "api_key_env": (
                                    "LOCAL_LLM_BENCHMARK_OPENAI_COMPAT_API_KEY"
                                ),
                            },
                        )
                    }
                )

    def test_build_provider_adapters_rejects_legacy_openai_compatible_api_key(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "api_key_env"):
            build_provider_adapters(
                {
                    "openai_compatible": ProviderProfile(
                        provider_id="openai_compatible",
                        connection={
                            "base_url": "http://localhost:1234/v1",
                            "api_key": "local-dummy",
                        },
                    )
                }
            )


if __name__ == "__main__":
    unittest.main()
