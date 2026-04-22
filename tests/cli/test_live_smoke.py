"""task_id 00008-01, 00011-02, 00016-02:
suites -> run -> report の opt-in live smoke。
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib import error, request

from local_llm_benchmark.cli.main import main
from local_llm_benchmark.config.loader import (
    build_benchmark_plan,
    load_config_bundle,
)
from local_llm_benchmark.providers.base import (
    ProviderConnectionError,
    ProviderResponseError,
)
from local_llm_benchmark.providers.ollama.client import OllamaClient
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry


LIVE_SMOKE_ENV_VAR = "LOCAL_LLM_BENCHMARK_RUN_LIVE_SMOKE"
LIVE_SMOKE_TRUE_VALUES = {"1", "true", "yes", "on"}
CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"
SUITE_ID = "local-three-tier-baseline-v1"
OPENAI_COMPAT_LIVE_SMOKE_ENV_VAR = (
    "LOCAL_LLM_BENCHMARK_RUN_OPENAI_COMPAT_LIVE_SMOKE"
)
OPENAI_COMPAT_SUITE_ID = "openai-compatible-minimal-v1"
OPENAI_COMPAT_MODEL_ALIAS = "llmb-minimal-chat"


def _live_smoke_enabled() -> bool:
    return (
        os.environ.get(LIVE_SMOKE_ENV_VAR, "").strip().lower()
        in LIVE_SMOKE_TRUE_VALUES
    )


def _openai_compatible_live_smoke_enabled() -> bool:
    return (
        os.environ.get(OPENAI_COMPAT_LIVE_SMOKE_ENV_VAR, "")
        .strip()
        .lower()
        in LIVE_SMOKE_TRUE_VALUES
    )


@unittest.skipUnless(
    _live_smoke_enabled(),
    (
        "task_id 00008-01: opt-in live smoke のため既定では実行しません。"
        f" {LIVE_SMOKE_ENV_VAR}=1 を設定してください。"
    ),
)
class LiveSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle = load_config_bundle(CONFIG_ROOT)
        cls._required_models = _resolve_required_model_names(bundle, SUITE_ID)
        profile = bundle.app_config.provider_profiles.get("ollama")
        if profile is None:
            raise unittest.SkipTest(
                "task_id 00008-01: provider profile 'ollama' が見つかりません。"
            )

        base_url = profile.connection.get("base_url")
        if not isinstance(base_url, str) or not base_url:
            raise unittest.SkipTest(
                "task_id 00008-01: Ollama 接続先 base_url が設定されていません。"
            )

        client = OllamaClient(
            base_url=base_url,
            timeout_seconds=_coerce_timeout_seconds(
                profile.connection.get("timeout_seconds")
            ),
        )
        _require_ollama_ready(client, cls._required_models)

    def test_suites_lists_available_suite(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "suites",
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=stderr,
        )

        output = stdout.getvalue()
        self.assertEqual(
            0,
            exit_code,
            msg=stderr.getvalue() or output,
        )
        self.assertIn("利用可能な suite:", output)
        self.assertIn(f"- {SUITE_ID}", output)
        self.assertIn(f"- {OPENAI_COMPAT_SUITE_ID}", output)

    def test_suites_shows_target_suite_detail(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "suites",
                SUITE_ID,
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=stderr,
        )

        output = stdout.getvalue()
        self.assertEqual(
            0,
            exit_code,
            msg=stderr.getvalue() or output,
        )
        self.assertIn(f"suite: {SUITE_ID}", output)
        for model_name in self._required_models:
            self.assertIn(model_name, output)

    def test_run_writes_result_artifacts(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_id = "task-00008-live-smoke"
            exit_code = main(
                [
                    "run",
                    "--config-root",
                    str(CONFIG_ROOT),
                    "--suite",
                    SUITE_ID,
                    "--run-id",
                    run_id,
                    "--output-dir",
                    temp_dir,
                ],
                stdout=stdout,
                stderr=stderr,
            )

            result_dir = Path(temp_dir) / run_id
            manifest_path = result_dir / "manifest.json"
            records_path = result_dir / "records.jsonl"
            case_evaluations_path = result_dir / "case-evaluations.jsonl"
            run_metrics_path = result_dir / "run-metrics.json"
            raw_dir = result_dir / "raw"

            self.assertEqual(
                0,
                exit_code,
                msg=stderr.getvalue() or stdout.getvalue(),
            )
            self.assertTrue(result_dir.is_dir())
            self.assertTrue(manifest_path.is_file())
            self.assertTrue(records_path.is_file())
            self.assertTrue(case_evaluations_path.is_file())
            self.assertTrue(run_metrics_path.is_file())
            self.assertTrue(raw_dir.is_dir())
            self.assertTrue(any(raw_dir.iterdir()))

            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(run_id, manifest["run_id"])
            self.assertEqual(SUITE_ID, manifest["suite_id"])
            self.assertTrue(records_path.read_text().splitlines())
            self.assertTrue(case_evaluations_path.read_text().splitlines())
            run_metrics = json.loads(run_metrics_path.read_text())
            self.assertEqual(run_id, run_metrics["run_id"])
            self.assertTrue(run_metrics["metrics"])

            report_stdout = io.StringIO()
            report_stderr = io.StringIO()
            report_exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(result_dir),
                ],
                stdout=report_stdout,
                stderr=report_stderr,
            )

            report_output = report_stdout.getvalue()
            self.assertEqual(
                0,
                report_exit_code,
                msg=report_stderr.getvalue() or report_output,
            )
            self.assertIn(f"run_id: {run_id}", report_output)
            self.assertIn(f"suite_id: {SUITE_ID}", report_output)
            self.assertIn("accuracy", report_output)
            self.assertIn("n=1", report_output)


@unittest.skipUnless(
    _openai_compatible_live_smoke_enabled(),
    (
        "task_id 00016-02: opt-in OpenAI-compatible live smoke のため既定では実行しません。"
        f" {OPENAI_COMPAT_LIVE_SMOKE_ENV_VAR}=1 を設定してください。"
    ),
)
class OpenAICompatibleLiveSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle = load_config_bundle(CONFIG_ROOT)
        cls._required_models = _resolve_required_model_names(
            bundle,
            OPENAI_COMPAT_SUITE_ID,
        )
        profile = bundle.app_config.provider_profiles.get("openai_compatible")
        if profile is None:
            raise unittest.SkipTest(
                "task_id 00016-02: provider profile "
                "'openai_compatible' が見つかりません。"
            )

        base_url = profile.connection.get("base_url")
        if not isinstance(base_url, str) or not base_url:
            raise unittest.SkipTest(
                "task_id 00016-02: OpenAI-compatible 接続先 base_url が設定されていません。"
            )

        timeout_seconds = _coerce_timeout_seconds(
            profile.connection.get("timeout_seconds")
        )
        api_key = _resolve_openai_compatible_api_key(profile.connection)
        _require_openai_compatible_ready(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            api_key=api_key,
            required_models=cls._required_models,
        )

    def test_suites_lists_available_suite(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "suites",
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=stderr,
        )

        output = stdout.getvalue()
        self.assertEqual(
            0,
            exit_code,
            msg=stderr.getvalue() or output,
        )
        self.assertIn("利用可能な suite:", output)
        self.assertIn(f"- {OPENAI_COMPAT_SUITE_ID}", output)

    def test_suites_shows_target_suite_detail(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = main(
            [
                "suites",
                OPENAI_COMPAT_SUITE_ID,
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=stderr,
        )

        output = stdout.getvalue()
        self.assertEqual(
            0,
            exit_code,
            msg=stderr.getvalue() or output,
        )
        self.assertIn(f"suite: {OPENAI_COMPAT_SUITE_ID}", output)
        for model_name in self._required_models:
            self.assertIn(model_name, output)

    def test_run_writes_result_artifacts(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_id = "task-00016-openai-compat-live-smoke"
            exit_code = main(
                [
                    "run",
                    "--config-root",
                    str(CONFIG_ROOT),
                    "--suite",
                    OPENAI_COMPAT_SUITE_ID,
                    "--run-id",
                    run_id,
                    "--output-dir",
                    temp_dir,
                ],
                stdout=stdout,
                stderr=stderr,
            )

            result_dir = Path(temp_dir) / run_id
            manifest_path = result_dir / "manifest.json"
            records_path = result_dir / "records.jsonl"
            case_evaluations_path = result_dir / "case-evaluations.jsonl"
            run_metrics_path = result_dir / "run-metrics.json"
            raw_dir = result_dir / "raw"

            self.assertEqual(
                0,
                exit_code,
                msg=stderr.getvalue() or stdout.getvalue(),
            )
            self.assertTrue(result_dir.is_dir())
            self.assertTrue(manifest_path.is_file())
            self.assertTrue(records_path.is_file())
            self.assertTrue(case_evaluations_path.is_file())
            self.assertTrue(run_metrics_path.is_file())
            self.assertTrue(raw_dir.is_dir())
            self.assertTrue(any(raw_dir.iterdir()))

            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(run_id, manifest["run_id"])
            self.assertEqual(OPENAI_COMPAT_SUITE_ID, manifest["suite_id"])
            self.assertTrue(records_path.read_text().splitlines())
            self.assertTrue(case_evaluations_path.read_text().splitlines())
            run_metrics = json.loads(run_metrics_path.read_text())
            self.assertEqual(run_id, run_metrics["run_id"])
            self.assertTrue(run_metrics["metrics"])

            report_stdout = io.StringIO()
            report_stderr = io.StringIO()
            report_exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(result_dir),
                ],
                stdout=report_stdout,
                stderr=report_stderr,
            )

            report_output = report_stdout.getvalue()
            self.assertEqual(
                0,
                report_exit_code,
                msg=report_stderr.getvalue() or report_output,
            )
            self.assertIn(f"run_id: {run_id}", report_output)
            self.assertIn(
                f"suite_id: {OPENAI_COMPAT_SUITE_ID}",
                report_output,
            )
            self.assertIn("accuracy", report_output)
            self.assertIn("json_valid_rate", report_output)
            self.assertIn("n=1", report_output)


def _resolve_required_model_names(
    bundle,
    suite_id: str,
) -> tuple[str, ...]:
    plan = build_benchmark_plan(
        bundle,
        suite_id=suite_id,
        run_id=f"task-{suite_id}-live-smoke-check",
    )
    registry = InMemoryModelRegistry(list(bundle.model_specs))
    return tuple(
        model.provider_model_name
        for model in registry.resolve_selector(plan.model_selector)
    )


def _require_ollama_ready(
    client: OllamaClient,
    required_models: tuple[str, ...],
) -> None:
    try:
        version = client.get_version()
    except ProviderConnectionError as exc:
        raise unittest.SkipTest(
            "task_id 00008-01: Ollama API に接続できません。"
            " Ollama を起動してから live smoke を再実行してください。"
        ) from exc
    except ProviderResponseError as exc:
        raise AssertionError(
            "task_id 00008-01: Ollama version 応答の確認に失敗しました: "
            f"{exc}"
        ) from exc

    if not isinstance(version.get("version"), str) or not version["version"]:
        raise AssertionError(
            "task_id 00008-01: Ollama version 応答に version がありません。"
        )

    try:
        available_models = _extract_model_names(client.list_local_models())
    except ProviderConnectionError as exc:
        raise unittest.SkipTest(
            "task_id 00008-01: Ollama tags API に接続できません。"
            " Ollama を起動してから live smoke を再実行してください。"
        ) from exc
    except ProviderResponseError as exc:
        raise AssertionError(
            "task_id 00008-01: Ollama tags 応答の確認に失敗しました: "
            f"{exc}"
        ) from exc

    missing_models = [
        model_name
        for model_name in required_models
        if model_name not in available_models
    ]
    if missing_models:
        raise unittest.SkipTest(
            "task_id 00008-01: live smoke に必要なモデルが不足しています。 "
            + ", ".join(missing_models)
        )


def _extract_model_names(payload: dict[str, object]) -> set[str]:
    records = payload.get("models")
    if not isinstance(records, list):
        raise AssertionError(
            "task_id 00008-01: Ollama tags 応答の models が配列ではありません。"
        )

    model_names: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in ("name", "model"):
            value = record.get(key)
            if isinstance(value, str) and value:
                model_names.add(value)
    return model_names


def _resolve_openai_compatible_api_key(
    connection: dict[str, object],
) -> str | None:
    if "api_key" in connection:
        raise AssertionError(
            "task_id 00016-02: live smoke は connection.api_key を使いません。"
        )

    api_key_env = connection.get("api_key_env")
    if api_key_env is None:
        return None
    if not isinstance(api_key_env, str) or not api_key_env:
        raise unittest.SkipTest(
            "task_id 00016-02: connection.api_key_env が不正です。"
        )

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise unittest.SkipTest(
            "task_id 00016-02: OpenAI-compatible 認証に必要な環境変数 "
            f"'{api_key_env}' が未設定または空文字です。"
        )
    return api_key


def _require_openai_compatible_ready(
    *,
    base_url: str,
    timeout_seconds: float,
    api_key: str | None,
    required_models: tuple[str, ...],
) -> None:
    try:
        available_models = _list_openai_compatible_models(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            api_key=api_key,
        )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise unittest.SkipTest(
            "task_id 00016-02: OpenAI-compatible /v1/models が HTTP "
            f"{exc.code} を返しました。 {body}"
        ) from exc
    except error.URLError as exc:
        raise unittest.SkipTest(
            "task_id 00016-02: OpenAI-compatible /v1/models に接続できません。"
            " server を起動して alias を load してから再実行してください。"
        ) from exc

    missing_models = [
        model_name
        for model_name in required_models
        if model_name not in available_models
    ]
    if missing_models:
        raise unittest.SkipTest(
            "task_id 00016-02: /v1/models に必要な alias がありません。 "
            + ", ".join(missing_models)
        )


def _list_openai_compatible_models(
    *,
    base_url: str,
    timeout_seconds: float,
    api_key: str | None,
) -> set[str]:
    headers = {"Accept": "application/json"}
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(
        url=f"{base_url.rstrip('/')}/models",
        headers=headers,
        method="GET",
    )
    with request.urlopen(req, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _extract_openai_compatible_model_ids(payload)


def _extract_openai_compatible_model_ids(payload: object) -> set[str]:
    if isinstance(payload, dict):
        records = payload.get("data")
        if not isinstance(records, list):
            records = payload.get("models")
    elif isinstance(payload, list):
        records = payload
    else:
        records = None

    if not isinstance(records, list):
        raise AssertionError(
            "task_id 00016-02: /v1/models 応答の data が配列ではありません。"
        )

    model_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in ("id", "model", "name"):
            value = record.get(key)
            if isinstance(value, str) and value:
                model_ids.add(value)
    return model_ids


def _coerce_timeout_seconds(value: object) -> float:
    if value is None:
        return 30.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise AssertionError(
        "task_id 00008-01: provider profile の timeout_seconds が不正です。"
    )


if __name__ == "__main__":
    unittest.main()
