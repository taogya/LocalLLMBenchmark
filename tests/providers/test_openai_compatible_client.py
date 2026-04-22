"""task_id 00010-02: OpenAICompatibleClient の HTTP 振る舞い確認。"""

from __future__ import annotations

from io import BytesIO
import json
import unittest
from unittest import mock
from urllib import error

from local_llm_benchmark.benchmark.models import GenerationSettings
from local_llm_benchmark.providers.base import (
    ProviderConnectionError,
    ProviderResponseError,
)
from local_llm_benchmark.providers.openai_compatible.client import (
    OpenAICompatibleClient,
)


class OpenAICompatibleClientTest(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    def test_chat_completions_posts_non_streaming_payload(
        self,
        mocked_urlopen: mock.Mock,
    ) -> None:
        response = mock.MagicMock()
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "ok"}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = response

        client = OpenAICompatibleClient(
            base_url="http://localhost:1234/v1",
            timeout_seconds=12.5,
            api_key="local-dummy",
        )

        payload = client.chat_completions(
            model_name="local-model",
            messages=[{"role": "user", "content": "hello"}],
            generation=GenerationSettings(
                temperature=0.1,
                top_p=0.8,
                max_tokens=32,
                seed=7,
                stop=("END",),
            ),
        )

        self.assertIn("choices", payload)
        req = mocked_urlopen.call_args.args[0]
        headers = {key.lower(): value for key, value in req.header_items()}
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(
            "http://localhost:1234/v1/chat/completions",
            req.full_url,
        )
        self.assertEqual("Bearer local-dummy", headers["authorization"])
        self.assertEqual("application/json", headers["content-type"])
        self.assertEqual("local-model", body["model"])
        self.assertEqual(False, body["stream"])
        self.assertEqual(0.1, body["temperature"])
        self.assertEqual(0.8, body["top_p"])
        self.assertEqual(32, body["max_tokens"])
        self.assertEqual(["END"], body["stop"])
        self.assertNotIn("seed", body)
        self.assertEqual(12.5, mocked_urlopen.call_args.kwargs["timeout"])

    @mock.patch("urllib.request.urlopen")
    def test_chat_completions_omits_authorization_without_api_key(
        self,
        mocked_urlopen: mock.Mock,
    ) -> None:
        response = mock.MagicMock()
        response.read.return_value = b"{}"
        mocked_urlopen.return_value.__enter__.return_value = response

        client = OpenAICompatibleClient(base_url="http://localhost:1234/v1")
        client.chat_completions(
            model_name="local-model",
            messages=[{"role": "user", "content": "hello"}],
        )

        req = mocked_urlopen.call_args.args[0]
        headers = {key.lower(): value for key, value in req.header_items()}
        self.assertNotIn("authorization", headers)

    @mock.patch("urllib.request.urlopen")
    def test_chat_completions_converts_http_error(
        self,
        mocked_urlopen: mock.Mock,
    ) -> None:
        mocked_urlopen.side_effect = error.HTTPError(
            url="http://localhost:1234/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":"invalid key"}'),
        )
        client = OpenAICompatibleClient(base_url="http://localhost:1234/v1")

        with self.assertRaisesRegex(
            ProviderResponseError,
            "HTTP 401",
        ):
            client.chat_completions(
                model_name="local-model",
                messages=[{"role": "user", "content": "hello"}],
            )

    @mock.patch("urllib.request.urlopen")
    def test_chat_completions_converts_connection_and_json_errors(
        self,
        mocked_urlopen: mock.Mock,
    ) -> None:
        client = OpenAICompatibleClient(base_url="http://localhost:1234/v1")

        mocked_urlopen.side_effect = error.URLError("refused")
        with self.assertRaisesRegex(
            ProviderConnectionError,
            "接続できません",
        ):
            client.chat_completions(
                model_name="local-model",
                messages=[{"role": "user", "content": "hello"}],
            )

        response = mock.MagicMock()
        response.read.return_value = b"not-json"
        mocked_urlopen.side_effect = None
        mocked_urlopen.return_value.__enter__.return_value = response
        with self.assertRaisesRegex(
            ProviderResponseError,
            "JSON 解析に失敗しました",
        ):
            client.chat_completions(
                model_name="local-model",
                messages=[{"role": "user", "content": "hello"}],
            )


if __name__ == "__main__":
    unittest.main()
