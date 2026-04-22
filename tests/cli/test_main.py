"""task_id 00004-02, 00006-03, 00007-02, 00011-02, 00015-02, 00016-02:
generic CLI の最小動作確認。
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from local_llm_benchmark.benchmark.models import InferenceResponse
from local_llm_benchmark.cli.main import build_parser, main


CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"
OPENAI_COMPAT_SUITE_ID = "openai-compatible-minimal-v1"


def _build_metric_row(
    *,
    model_key: str,
    prompt_category: str,
    prompt_id: str,
    metric_name: str,
    value: float,
    threshold: object,
    passed: bool | None,
    sample_count: int,
) -> dict[str, object]:
    return {
        "scope": {
            "model_key": model_key,
            "prompt_category": prompt_category,
            "prompt_id": prompt_id,
        },
        "metric_name": metric_name,
        "scorer_name": "test-scorer",
        "scorer_version": "v1",
        "aggregation": "mean",
        "value": value,
        "threshold": threshold,
        "passed": passed,
        "sample_count": sample_count,
        "evaluation_mode": "auto",
    }


def _write_report_artifacts(
    run_dir: Path,
    *,
    run_id: str = "cli-test-run",
    run_metrics_run_id: str | None = None,
    suite_id: str = "suite-1",
    record_count: int = 1,
    metrics: list[dict[str, object]] | None = None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "result-sink.v1",
        "run_id": run_id,
        "suite_id": suite_id,
        "status": "completed",
        "record_count": record_count,
    }
    run_metrics = {
        "schema_version": "run-metrics.v1",
        "run_id": run_metrics_run_id or run_id,
        "metrics": metrics or [],
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "run-metrics.json").write_text(
        json.dumps(run_metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class FakeProviderAdapter:
    provider_id = "ollama"

    def __init__(self) -> None:
        self.requests = []

    def infer(self, request):
        self.requests.append(request)
        return InferenceResponse(
            output_text=(
                f"task_id 00004-02: {request.model.model_key} / "
                f"{request.prompt.prompt_id}"
            ),
            raw_response={"ok": True},
        )


class CliMainTest(unittest.TestCase):
    def test_help_is_provider_neutral(self) -> None:
        parser = build_parser()
        run_parser = next(
            action.choices["run"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )
        suites_parser = next(
            action.choices["suites"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )
        report_parser = next(
            action.choices["report"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )
        compare_parser = next(
            action.choices["compare"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )
        output = parser.format_help() + run_parser.format_help()
        output += suites_parser.format_help() + report_parser.format_help()
        output += compare_parser.format_help()
        self.assertIn("run", output)
        self.assertIn("suites", output)
        self.assertIn("report", output)
        self.assertIn("compare", output)
        self.assertIn("--config-root", output)
        self.assertIn("--run-dir", output)
        self.assertNotIn("task_id", output)
        self.assertNotIn("ollama", output.lower())

    def test_report_help_lists_run_dir_option(self) -> None:
        parser = build_parser()
        report_parser = next(
            action.choices["report"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )

        output = report_parser.format_help()

        self.assertIn("--run-dir", output)
        self.assertIn("保存済み run の metric 要約を表示する", output)

    def test_compare_help_lists_run_dir_option(self) -> None:
        parser = build_parser()
        compare_parser = next(
            action.choices["compare"]
            for action in parser._actions
            if getattr(action, "choices", None)
        )

        output = compare_parser.format_help()

        self.assertIn("--run-dir", output)
        self.assertIn("先頭を baseline", output)
        self.assertIn("保存済み run の metric 差分を表示する", output)

    def test_suites_lists_available_suite_summary(self) -> None:
        stdout = io.StringIO()

        exit_code = main(
            [
                "suites",
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=io.StringIO(),
        )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("利用可能な suite:", output)
        self.assertIn("- local-three-tier-baseline-v1", output)
        self.assertIn(f"- {OPENAI_COMPAT_SUITE_ID}", output)
        self.assertIn("3 ランク各 1 モデルで比較する初期 baseline。", output)
        self.assertIn(
            "3 モデル / 6 プロンプト / provider: ollama",
            output,
        )
        self.assertIn(
            "1 モデル / 3 プロンプト / provider: openai_compatible",
            output,
        )
        self.assertIn(
            "local-llm-benchmark suites local-three-tier-baseline-v1",
            output,
        )
        self.assertNotIn("ollama pull", output)

    def test_suites_shows_suite_detail(self) -> None:
        stdout = io.StringIO()

        exit_code = main(
            [
                "suites",
                "local-three-tier-baseline-v1",
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=io.StringIO(),
        )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("suite: local-three-tier-baseline-v1", output)
        self.assertIn("概要: 3 ランク各 1 モデルで比較する初期 baseline。", output)
        self.assertIn("tags: baseline, three-tier", output)
        self.assertIn("- prompt set: core-small-model-ja-v1", output)
        self.assertIn("- resolved prompts: 6", output)
        self.assertIn(
            (
                "- categories: classification, constrained_generation, "
                "extraction, rewrite, short_qa, summarization"
            ),
            output,
        )
        self.assertIn(
            "- ollama: gemma3:latest, qwen2.5:7b, llama3.1:8b",
            output,
        )
        self.assertIn(
            "local-llm-benchmark run --config-root",
            output,
        )
        self.assertNotIn("ollama pull", output)

    def test_suites_shows_openai_compatible_minimal_suite_detail(self) -> None:
        stdout = io.StringIO()

        exit_code = main(
            [
                "suites",
                OPENAI_COMPAT_SUITE_ID,
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=stdout,
            stderr=io.StringIO(),
        )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn(f"suite: {OPENAI_COMPAT_SUITE_ID}", output)
        self.assertIn(
            "概要: OpenAI-compatible readiness 用の 1 model x 3 prompts 最小 suite。",
            output,
        )
        self.assertIn(
            "tags: minimal, openai-compatible, readiness",
            output,
        )
        self.assertIn("- prompt set: minimal-readiness-ja-v1", output)
        self.assertIn("- resolved prompts: 3", output)
        self.assertIn(
            "- categories: classification, extraction, short_qa",
            output,
        )
        self.assertIn("- openai_compatible: llmb-minimal-chat", output)
        self.assertIn(
            "local-llm-benchmark run --config-root",
            output,
        )

    def test_suites_returns_error_for_unknown_suite(self) -> None:
        stderr = io.StringIO()

        exit_code = main(
            [
                "suites",
                "missing-suite",
                "--config-root",
                str(CONFIG_ROOT),
            ],
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertEqual(1, exit_code)
        self.assertIn(
            "suite_id 'missing-suite' は config bundle に存在しません。",
            stderr.getvalue(),
        )

    def test_run_executes_suite_from_external_config(self) -> None:
        adapter = FakeProviderAdapter()
        stdout = io.StringIO()
        with TemporaryDirectory() as temp_dir:
            with mock.patch(
                "local_llm_benchmark.cli.main.build_provider_adapters",
                return_value={"ollama": adapter},
            ):
                exit_code = main(
                    [
                        "run",
                        "--config-root",
                        str(CONFIG_ROOT),
                        "--suite",
                        "local-three-tier-baseline-v1",
                        "--run-id",
                        "cli-test-run",
                        "--output-dir",
                        temp_dir,
                    ],
                    stdout=stdout,
                    stderr=io.StringIO(),
                )

            result_dir = Path(temp_dir) / "cli-test-run"
            self.assertTrue((result_dir / "manifest.json").exists())
            self.assertTrue((result_dir / "records.jsonl").exists())
            self.assertTrue((result_dir / "case-evaluations.jsonl").exists())
            self.assertTrue((result_dir / "run-metrics.json").exists())
            self.assertTrue((result_dir / "raw").is_dir())

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("run_id: cli-test-run", output)
        self.assertIn("suite_id: local-three-tier-baseline-v1", output)
        self.assertIn("result_dir:", output)
        self.assertIn("records: 18", output)
        self.assertIn("errors: 0", output)
        self.assertIn("local.entry.gemma3", output)
        self.assertIn("contact-routing-v1", output)
        self.assertEqual(18, len(adapter.requests))

    def test_report_reads_single_run_metrics(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "cli-test-run"
            _write_report_artifacts(
                run_dir,
                run_id="cli-test-run",
                suite_id="suite-report",
                record_count=1,
                metrics=[
                    _build_metric_row(
                        model_key="local.entry.gemma3",
                        prompt_category="classification",
                        prompt_id="contact-routing-v1",
                        metric_name="accuracy",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    )
                ],
            )

            exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("run_id: cli-test-run", output)
        self.assertIn("suite_id: suite-report", output)
        self.assertIn(f"run_dir: {run_dir}", output)
        self.assertIn("records: 1", output)
        self.assertIn("metric_rows: 1", output)
        self.assertIn(
            (
                "legend: records=manifest.record_count, "
                "scope=model_key | prompt_category | prompt_id, "
                "n=sample_count, passed=n/a when run threshold is not "
                "evaluated"
            ),
            output,
        )
        self.assertIn(
            (
                "- local.entry.gemma3 | classification | "
                "contact-routing-v1 | accuracy | value=1.000 | "
                "threshold=- | passed=n/a | n=1"
            ),
            output,
        )
        self.assertNotIn("note:", output)

    def test_report_formats_threshold_and_passed_columns(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "cli-test-run"
            _write_report_artifacts(
                run_dir,
                record_count=4,
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="accuracy",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    ),
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="extraction",
                        prompt_id="prompt-b",
                        metric_name="json_valid_rate",
                        value=1.0,
                        threshold={"type": "min", "value": 1.0},
                        passed=True,
                        sample_count=1,
                    ),
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="rewrite",
                        prompt_id="prompt-c",
                        metric_name="constraint_pass_rate",
                        value=0.0,
                        threshold={"type": "min", "value": 1.0},
                        passed=False,
                        sample_count=1,
                    ),
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="summarization",
                        prompt_id="prompt-d",
                        metric_name="length_compliance_rate",
                        value=1.0,
                        threshold={
                            "type": "range",
                            "min": 80,
                            "max": 120,
                            "unit": "chars",
                        },
                        passed=None,
                        sample_count=1,
                    ),
                ],
            )

            exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("threshold=- | passed=n/a", output)
        self.assertIn("threshold=>=1.0 | passed=pass", output)
        self.assertIn("threshold=>=1.0 | passed=fail", output)
        self.assertIn(
            "threshold=80-120 chars | passed=n/a",
            output,
        )

    def test_compare_renders_differing_rows_against_baseline(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            baseline_run_dir = Path(temp_dir) / "run-a"
            candidate_run_dir = Path(temp_dir) / "run-b"
            _write_report_artifacts(
                baseline_run_dir,
                run_id="run-a",
                suite_id="suite-compare",
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="accuracy",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    )
                ],
            )
            _write_report_artifacts(
                candidate_run_dir,
                run_id="run-b",
                suite_id="suite-compare",
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="accuracy",
                        value=0.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    )
                ],
            )

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(baseline_run_dir),
                    "--run-dir",
                    str(candidate_run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("baseline_run_id: run-a", output)
        self.assertIn("suite_id: suite-compare", output)
        self.assertIn("compare_run_ids: run-b", output)
        self.assertIn("differing_rows: 1", output)
        self.assertIn("identical_rows_omitted: 0", output)
        self.assertIn(
            (
                "- model-a | classification | prompt-a | accuracy | "
                "threshold=- | base=1.000 | run-b=0.000 | delta=-1.000 | "
                "base_pass=n/a | run-b_pass=n/a | base_n=1 | run-b_n=1"
            ),
            output,
        )

    def test_compare_omits_identical_rows_from_default_output(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            baseline_run_dir = Path(temp_dir) / "run-a"
            candidate_run_dir = Path(temp_dir) / "run-b"
            baseline_metrics = [
                _build_metric_row(
                    model_key="model-a",
                    prompt_category="classification",
                    prompt_id="prompt-a",
                    metric_name="accuracy",
                    value=1.0,
                    threshold=None,
                    passed=None,
                    sample_count=1,
                ),
                _build_metric_row(
                    model_key="model-a",
                    prompt_category="classification",
                    prompt_id="prompt-a",
                    metric_name="macro_f1",
                    value=0.5,
                    threshold=None,
                    passed=None,
                    sample_count=1,
                ),
            ]
            candidate_metrics = [
                _build_metric_row(
                    model_key="model-a",
                    prompt_category="classification",
                    prompt_id="prompt-a",
                    metric_name="accuracy",
                    value=0.0,
                    threshold=None,
                    passed=None,
                    sample_count=1,
                ),
                _build_metric_row(
                    model_key="model-a",
                    prompt_category="classification",
                    prompt_id="prompt-a",
                    metric_name="macro_f1",
                    value=0.5,
                    threshold=None,
                    passed=None,
                    sample_count=1,
                ),
            ]
            _write_report_artifacts(
                baseline_run_dir,
                run_id="run-a",
                suite_id="suite-compare",
                metrics=baseline_metrics,
            )
            _write_report_artifacts(
                candidate_run_dir,
                run_id="run-b",
                suite_id="suite-compare",
                metrics=candidate_metrics,
            )

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(baseline_run_dir),
                    "--run-dir",
                    str(candidate_run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("differing_rows: 1", output)
        self.assertIn("identical_rows_omitted: 1", output)
        self.assertIn("| accuracy |", output)
        self.assertNotIn("| macro_f1 |", output)

    def test_compare_marks_missing_rows_and_suite_mismatch(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            baseline_run_dir = Path(temp_dir) / "run-a"
            candidate_run_dir = Path(temp_dir) / "run-b"
            _write_report_artifacts(
                baseline_run_dir,
                run_id="run-a",
                suite_id="suite-a",
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="accuracy",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    )
                ],
            )
            _write_report_artifacts(
                candidate_run_dir,
                run_id="run-b",
                suite_id="suite-b",
                metrics=[],
            )

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(baseline_run_dir),
                    "--run-dir",
                    str(candidate_run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn(
            "note: suite_id mismatch: suite-a, suite-b.",
            output,
        )
        self.assertIn(
            "note: missing は run error、auto 評価対象外、suite / plan 差分",
            output,
        )
        self.assertIn(
            "base=1.000 | run-b=missing | delta=n/a",
            output,
        )
        self.assertIn(
            "base_pass=n/a | run-b_pass=missing | base_n=1 | run-b_n=missing",
            output,
        )

    def test_compare_marks_threshold_varies(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            baseline_run_dir = Path(temp_dir) / "run-a"
            candidate_run_dir = Path(temp_dir) / "run-b"
            _write_report_artifacts(
                baseline_run_dir,
                run_id="run-a",
                suite_id="suite-compare",
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="extraction",
                        prompt_id="prompt-a",
                        metric_name="json_valid_rate",
                        value=1.0,
                        threshold={"type": "min", "value": 1.0},
                        passed=True,
                        sample_count=1,
                    )
                ],
            )
            _write_report_artifacts(
                candidate_run_dir,
                run_id="run-b",
                suite_id="suite-compare",
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="extraction",
                        prompt_id="prompt-a",
                        metric_name="json_valid_rate",
                        value=1.0,
                        threshold={"type": "min", "value": 0.9},
                        passed=True,
                        sample_count=1,
                    )
                ],
            )

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(baseline_run_dir),
                    "--run-dir",
                    str(candidate_run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("differing_rows: 1", output)
        self.assertIn("threshold=varies", output)
        self.assertIn("base=1.000 | run-b=1.000 | delta=+0.000", output)

    def test_compare_returns_error_for_duplicate_paths(self) -> None:
        stderr = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run-a"
            _write_report_artifacts(run_dir, run_id="run-a")

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(run_dir),
                    "--run-dir",
                    str(run_dir),
                ],
                stdout=io.StringIO(),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertIn("compare の --run-dir に重複パスがあります", stderr.getvalue())

    def test_compare_returns_error_for_duplicate_run_ids(self) -> None:
        stderr = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            first_run_dir = Path(temp_dir) / "run-a"
            second_run_dir = Path(temp_dir) / "run-b"
            _write_report_artifacts(first_run_dir, run_id="same-run")
            _write_report_artifacts(second_run_dir, run_id="same-run")

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(first_run_dir),
                    "--run-dir",
                    str(second_run_dir),
                ],
                stdout=io.StringIO(),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertIn("compare の run_id が重複しています", stderr.getvalue())

    def test_compare_includes_strict_gate_note(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            baseline_run_dir = Path(temp_dir) / "run-a"
            candidate_run_dir = Path(temp_dir) / "run-b"
            metrics = [
                _build_metric_row(
                    model_key="model-a",
                    prompt_category="constrained_generation",
                    prompt_id="prompt-a",
                    metric_name="constraint_pass_rate",
                    value=1.0,
                    threshold=None,
                    passed=None,
                    sample_count=1,
                )
            ]
            _write_report_artifacts(
                baseline_run_dir,
                run_id="run-a",
                suite_id="suite-compare",
                metrics=metrics,
            )
            _write_report_artifacts(
                candidate_run_dir,
                run_id="run-b",
                suite_id="suite-compare",
                metrics=metrics,
            )

            exit_code = main(
                [
                    "compare",
                    "--run-dir",
                    str(baseline_run_dir),
                    "--run-dir",
                    str(candidate_run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn(
            (
                "note: json_valid_rate / format_valid_rate は raw "
                "JSON-only contract を見る strict gate、"
            ),
            output,
        )
        self.assertIn(
            (
                "constraint_pass_rate は exact lexical / structural "
                "contract を見る strict gate"
            ),
            output,
        )
        self.assertIn("differing_rows: 0", output)
        self.assertIn("identical_rows_omitted: 1", output)

    def test_report_returns_error_for_missing_artifacts(self) -> None:
        for missing_file in ("manifest.json", "run-metrics.json"):
            with self.subTest(missing_file=missing_file):
                stderr = io.StringIO()
                with TemporaryDirectory() as temp_dir:
                    run_dir = Path(temp_dir) / "cli-test-run"
                    run_dir.mkdir(parents=True, exist_ok=True)
                    if missing_file != "manifest.json":
                        _write_report_artifacts(run_dir)
                        (run_dir / "run-metrics.json").unlink()
                    else:
                        (run_dir / "run-metrics.json").write_text(
                            json.dumps(
                                {
                                    "schema_version": "run-metrics.v1",
                                    "run_id": "cli-test-run",
                                    "metrics": [],
                                },
                                ensure_ascii=False,
                                indent=2,
                            )
                            + "\n",
                            encoding="utf-8",
                        )

                    exit_code = main(
                        [
                            "report",
                            "--run-dir",
                            str(run_dir),
                        ],
                        stdout=io.StringIO(),
                        stderr=stderr,
                    )

                self.assertEqual(1, exit_code)
                self.assertIn(missing_file, stderr.getvalue())

    def test_report_returns_error_for_mismatched_run_ids(self) -> None:
        stderr = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "cli-test-run"
            _write_report_artifacts(
                run_dir,
                run_id="manifest-run",
                run_metrics_run_id="metrics-run",
            )

            exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(run_dir),
                ],
                stdout=io.StringIO(),
                stderr=stderr,
            )

        self.assertEqual(1, exit_code)
        self.assertIn(
            "manifest.json と run-metrics.json の run_id が一致しません。",
            stderr.getvalue(),
        )

    def test_report_shows_informational_note_for_scope_mismatch(self) -> None:
        stdout = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "cli-test-run"
            _write_report_artifacts(
                run_dir,
                record_count=2,
                metrics=[
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="accuracy",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    ),
                    _build_metric_row(
                        model_key="model-a",
                        prompt_category="classification",
                        prompt_id="prompt-a",
                        metric_name="macro_f1",
                        value=1.0,
                        threshold=None,
                        passed=None,
                        sample_count=1,
                    ),
                ],
            )

            exit_code = main(
                [
                    "report",
                    "--run-dir",
                    str(run_dir),
                ],
                stdout=stdout,
                stderr=io.StringIO(),
            )

        output = stdout.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn(
            "note: manifest.record_count=2, metric scopes=1.",
            output,
        )
        self.assertIn(
            "sample_count は各 metric 行に寄与した case 数で、",
            output,
        )


if __name__ == "__main__":
    unittest.main()
