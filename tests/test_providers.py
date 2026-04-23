"""Provider Adapter (Ollama) のユニットテスト.

対応 ID: COMP-00005, PVD-00001, PVD-00004, PVD-00106..00110,
    PVD-00201..00215, PVD-00301..00305, FUN-00408, FUN-00409,
    FUN-00410, NFR-00302

実 HTTP 通信は行わず、urllib.request.urlopen をモンキーパッチして
Adapter の標準化レスポンス変換ロジックを検証する。
"""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
import urllib.request
from typing import Callable
from unittest.mock import patch

from local_llm_benchmark.models import (
    GenerationConditions,
    InferenceRequest,
    ProviderEndpoint,
)
from local_llm_benchmark.providers import (
    FAILURE_MODEL_NOT_FOUND,
    FAILURE_PROVIDER_UNREACHABLE,
    FAILURE_TIMEOUT,
    FAILURE_UNSUPPORTED_REQUEST,
    MODEL_AVAILABLE,
    MODEL_MISSING,
    PROBE_REACHABLE,
    PROBE_UNREACHABLE,
)
from local_llm_benchmark.providers.ollama import OllamaAdapter


class _FakeHTTPResponse(io.BytesIO):
    def __enter__(self):  # noqa: D401
        return self

    def __exit__(self, *_a):  # noqa: D401
        self.close()
        return False


def _make_request() -> InferenceRequest:
    return InferenceRequest(
        prompt="hello",
        generation=GenerationConditions(temperature=0.0, seed=1, max_tokens=8),
        model_ref="qwen2:1.5b",
        timeout_seconds=10.0,
        run_id="run-x",
        task_profile_name="tp",
        case_name="c",
        trial_index=1,
    )


def _patched_urlopen(
    handler: Callable[[urllib.request.Request], _FakeHTTPResponse],
):
    return patch.object(urllib.request, "urlopen", handler)


class TestOllamaAdapterSuccess(unittest.TestCase):
    def test_returns_standardized_response(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            payload = json.dumps(
                {
                    "model": "qwen2:1.5b",
                    "response": "world",
                    "prompt_eval_count": 3,
                    "eval_count": 5,
                    "done": True,
                }
            ).encode("utf-8")
            return _FakeHTTPResponse(payload)

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertIsNone(resp.failure_kind)
        self.assertEqual(resp.response_text, "world")
        self.assertEqual(resp.input_tokens, 3)
        self.assertEqual(resp.output_tokens, 5)
        self.assertIsNotNone(resp.elapsed_seconds)
        # PVD-00208 provider 識別
        self.assertEqual(resp.provider_identity["kind"], "ollama")
        self.assertEqual(resp.provider_identity["model_ref"], "qwen2:1.5b")
        # PVD-00205 生応答が保存されている
        self.assertEqual(resp.raw_response["response"], "world")

    def test_missing_response_key_is_malformed(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            return _FakeHTTPResponse(b'{"done": true}')

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertEqual(resp.failure_kind, "malformed_response")

    def test_probe_resolves_inventory(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            payload = json.dumps(
                {
                    "models": [
                        {"name": "qwen2:1.5b", "size": 123},
                        {"name": "phi3:mini", "size": 456},
                    ]
                }
            ).encode("utf-8")
            return _FakeHTTPResponse(payload)

        with _patched_urlopen(handler):
            provider, models = adapter.probe(["qwen2:1.5b", "missing:model"])
        self.assertEqual(provider.status, PROBE_REACHABLE)
        self.assertEqual(models["qwen2:1.5b"].status, MODEL_AVAILABLE)
        self.assertEqual(models["missing:model"].status, MODEL_MISSING)

    def test_status_returns_version_and_inventory(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            if req.full_url.endswith("/api/tags"):
                return _FakeHTTPResponse(
                    json.dumps(
                        {
                            "models": [
                                {"name": "qwen2:1.5b", "size": 123},
                                {"name": "phi3:mini", "size": 456},
                            ]
                        }
                    ).encode("utf-8")
                )
            if req.full_url.endswith("/api/version"):
                return _FakeHTTPResponse(
                    json.dumps({"version": "0.6.0"}).encode("utf-8")
                )
            raise AssertionError(f"unexpected url: {req.full_url}")

        with _patched_urlopen(handler):
            result = adapter.status()
        self.assertEqual(result.status, PROBE_REACHABLE)
        self.assertEqual(result.version_info["version"], "0.6.0")
        self.assertEqual(len(result.inventory), 2)

    def test_pull_returns_already_present_without_post(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            if req.full_url.endswith("/api/tags"):
                return _FakeHTTPResponse(
                    json.dumps(
                        {"models": [{"name": "qwen2:1.5b", "size": 123}]}
                    ).encode("utf-8")
                )
            if req.full_url.endswith("/api/version"):
                return _FakeHTTPResponse(
                    json.dumps({"version": "0.6.0"}).encode("utf-8")
                )
            raise AssertionError(f"unexpected url: {req.full_url}")

        with _patched_urlopen(handler):
            result = adapter.pull("qwen2:1.5b")
        self.assertEqual(result.state, "already_present")
        self.assertEqual(result.detail, "provider inventory で既に利用可能")

    def test_pull_streams_progress(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))
        seen_statuses: list[str] = []

        def handler(req, timeout=None):  # noqa: ARG001
            if req.full_url.endswith("/api/tags"):
                return _FakeHTTPResponse(
                    json.dumps({"models": []}).encode("utf-8")
                )
            if req.full_url.endswith("/api/version"):
                return _FakeHTTPResponse(
                    json.dumps({"version": "0.6.0"}).encode("utf-8")
                )
            if req.full_url.endswith("/api/pull"):
                return _FakeHTTPResponse(
                    b'{"status":"pulling manifest"}\n'
                    + (
                        b'{"status":"pulling digest","digest":"sha256:x",'
                        b'"total":10,"completed":4}\n'
                    )
                    + b'{"status":"success"}\n'
                )
            raise AssertionError(f"unexpected url: {req.full_url}")

        with _patched_urlopen(handler):
            result = adapter.pull(
                "qwen2:1.5b",
                on_progress=lambda event: seen_statuses.append(event.status),
            )
        self.assertEqual(result.state, "succeeded")
        self.assertEqual(seen_statuses, [
            "pulling manifest", "pulling digest", "success"
        ])
        self.assertEqual(result.progress[1].completed, 4)

    def test_warmup_loads_model_with_empty_prompt(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            payload = json.loads(req.data.decode("utf-8"))
            self.assertEqual(payload["model"], "qwen2:1.5b")
            self.assertEqual(payload["prompt"], "")
            self.assertFalse(payload["stream"])
            return _FakeHTTPResponse(
                json.dumps(
                    {
                        "model": "qwen2:1.5b",
                        "response": "",
                        "done": True,
                        "done_reason": "load",
                        "load_duration": 123,
                    }
                ).encode("utf-8")
            )

        with _patched_urlopen(handler):
            result = adapter.warmup("qwen2:1.5b")
        self.assertEqual(result.state, "ready")
        self.assertEqual(result.metadata["done_reason"], "load")


class TestOllamaAdapterFailure(unittest.TestCase):
    def test_404_maps_to_model_not_found(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            raise urllib.error.HTTPError(
                req.full_url,
                404,
                "Not Found",
                hdrs={},
                fp=io.BytesIO(b"missing"),
            )

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertEqual(resp.failure_kind, FAILURE_MODEL_NOT_FOUND)

    def test_url_error_maps_to_unreachable(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            raise urllib.error.URLError("Connection refused")

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertEqual(resp.failure_kind, FAILURE_PROVIDER_UNREACHABLE)

    def test_timeout_maps_to_timeout(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            raise urllib.error.URLError(TimeoutError("timed out"))

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertEqual(resp.failure_kind, FAILURE_TIMEOUT)

    def test_probe_url_error_maps_to_unreachable(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            raise urllib.error.URLError("Connection refused")

        with _patched_urlopen(handler):
            provider, models = adapter.probe(["qwen2:1.5b"])
        self.assertEqual(provider.status, PROBE_UNREACHABLE)
        self.assertEqual(models["qwen2:1.5b"].status, "unknown")


class TestOllamaAdapterUnsupportedRequest(unittest.TestCase):
    """PVD-00306 unsupported_request の検知 (TASK-00007-03)."""

    def _bad_request(
        self,
        *,
        temperature: float | None = 0.0,
        max_tokens: int | None = 8,
        prompt: str = "hello",
        model_ref: str = "qwen2:1.5b",
    ) -> InferenceRequest:
        return InferenceRequest(
            prompt=prompt,
            generation=GenerationConditions(
                temperature=temperature, seed=1, max_tokens=max_tokens,
            ),
            model_ref=model_ref,
            timeout_seconds=10.0,
            run_id="run-x",
            task_profile_name="tp",
            case_name="c",
            trial_index=1,
        )

    def test_negative_temperature_is_unsupported(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))
        # 事前検査で provider 呼び出し前に弾く: urlopen にパッチ不要
        resp = adapter.infer(self._bad_request(temperature=-0.5))
        self.assertEqual(resp.failure_kind, FAILURE_UNSUPPORTED_REQUEST)
        self.assertIn("temperature", resp.failure_detail or "")

    def test_zero_max_tokens_is_unsupported(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))
        resp = adapter.infer(self._bad_request(max_tokens=0))
        self.assertEqual(resp.failure_kind, FAILURE_UNSUPPORTED_REQUEST)

    def test_empty_prompt_is_unsupported(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))
        resp = adapter.infer(self._bad_request(prompt=""))
        self.assertEqual(resp.failure_kind, FAILURE_UNSUPPORTED_REQUEST)

    def test_http_400_maps_to_unsupported(self) -> None:
        adapter = OllamaAdapter(ProviderEndpoint(kind="ollama"))

        def handler(req, timeout=None):  # noqa: ARG001
            raise urllib.error.HTTPError(
                req.full_url, 400, "Bad Request",
                hdrs={}, fp=io.BytesIO(b"unsupported"),
            )

        with _patched_urlopen(handler):
            resp = adapter.infer(_make_request())
        self.assertEqual(resp.failure_kind, FAILURE_UNSUPPORTED_REQUEST)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
