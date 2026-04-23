"""CLI list / runs / check / config lint / config dry-run / provider status /
model pull / model warmup / 終了コードのテスト (
TASK-00007-03, TASK-00013-02).

対応 ID: CLI-00103, CLI-00104, CLI-00105, CLI-00109, CLI-00110, CLI-00111,
CLI-00112, CLI-00113, CLI-00114, CLI-00301, CLI-00302, CLI-00303,
CLI-00307, CLI-00308, CLI-00309, FUN-00104, FUN-00105, FUN-00401,
FUN-00402, FUN-00404, FUN-00405, FUN-00406, FUN-00407, FUN-00408,
FUN-00409, FUN-00410, CFG-00501..00506, NFR-00302
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from local_llm_benchmark.cli.main import (
    EXIT_CONFIGURATION_ERROR,
    EXIT_DRY_RUN_NEGATIVE,
    EXIT_PROVIDER_STATUS_NEGATIVE,
    EXIT_PROBE_NEGATIVE,
    EXIT_RUNTIME_ERROR,
    EXIT_SUCCESS,
    EXIT_USER_INPUT_ERROR,
    main,
)
from local_llm_benchmark.providers import (
    MODEL_AVAILABLE,
    MODEL_MISSING,
    PROBE_UNKNOWN,
    PullProgress,
    PullResult,
    PROBE_REACHABLE,
    ProviderStatusResult,
    ProviderProbeResult,
    WarmupResult,
    ModelProbeResult,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _materialize_valid_cfg(td: Path) -> Path:
    cfg_dir = td / "cfg"
    _write(
        cfg_dir / "task_profiles" / "qa.toml",
        """
[task_profile]
name = "qa-basic"
purpose = "qa"

[task_profile.scorer]
name = "exact_match"

[[task_profile.cases]]
name = "c1"
input = "1+1?"
expected_output = "2"
""",
    )
    _write(
        cfg_dir / "model_candidates.toml",
        """
[[model_candidate]]
name = "stub"
provider_kind = "ollama"
provider_model_ref = "stub:tiny"
""",
    )
    _write(
        cfg_dir / "providers.toml",
        """
[[provider]]
kind = "ollama"
host = "localhost"
port = 11434
""",
    )
    return cfg_dir


def _materialize_probe_cfg(td: Path) -> Path:
    cfg_dir = td / "cfg"
    _write(
        cfg_dir / "model_candidates.toml",
        """
[[model_candidate]]
name = "stub"
provider_kind = "ollama"
provider_model_ref = "stub:tiny"
""",
    )
    _write(
        cfg_dir / "providers.toml",
        """
[[provider]]
kind = "ollama"
host = "localhost"
port = 11434
""",
    )
    return cfg_dir


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


class _StubProbeAdapter:
    def __init__(
        self,
        *,
        provider_status: str = PROBE_REACHABLE,
        model_status: str = MODEL_AVAILABLE,
        validate_detail: str | None = None,
        pull_state: str = "succeeded",
        warmup_state: str = "ready",
    ) -> None:
        self.provider_status = provider_status
        self.model_status = model_status
        self.validate_detail = validate_detail
        self.pull_state = pull_state
        self.warmup_state = warmup_state

    def probe(
        self,
        model_refs: list[str],
    ) -> tuple[ProviderProbeResult, dict[str, ModelProbeResult]]:
        provider = ProviderProbeResult(
            status=self.provider_status,
            detail="stub provider probe",
            raw_response={"stub": True},
            provider_identity={
                "kind": "ollama",
                "host": "localhost",
                "port": 11434,
                "model_ref": None,
            },
            metadata={"inventory_count": len(model_refs)},
        )
        models = {
            ref: ModelProbeResult(
                model_ref=ref,
                status=self.model_status,
                detail=f"stub {self.model_status}",
                raw_response={"ref": ref},
                provider_identity={
                    "kind": "ollama",
                    "host": "localhost",
                    "port": 11434,
                    "model_ref": ref,
                },
            )
            for ref in model_refs
        }
        return provider, models

    def validate_request(self, _request) -> str | None:
        return self.validate_detail

    def status(self) -> ProviderStatusResult:
        inventory = []
        if self.provider_status == PROBE_REACHABLE:
            inventory.append({"name": "stub:tiny", "size": 123})
        return ProviderStatusResult(
            status=self.provider_status,
            detail="stub provider status",
            raw_response={"stub": True},
            provider_identity={
                "kind": "ollama",
                "host": "localhost",
                "port": 11434,
                "model_ref": None,
            },
            version_info={"version": "0.6.0"},
            inventory=tuple(inventory),
        )

    def pull(self, model_ref, on_progress=None) -> PullResult:
        progress = []
        if self.pull_state == "succeeded":
            progress = [
                PullProgress(
                    status="pulling manifest",
                    digest=None,
                    total=None,
                    completed=None,
                    raw_response={"status": "pulling manifest"},
                ),
                PullProgress(
                    status="success",
                    digest=None,
                    total=10,
                    completed=10,
                    raw_response={
                        "status": "success",
                        "total": 10,
                        "completed": 10,
                    },
                ),
            ]
        for event in progress:
            if on_progress is not None:
                on_progress(event)
        return PullResult(
            state=self.pull_state,
            detail=f"stub pull {self.pull_state}",
            raw_response={"model_ref": model_ref},
            provider_identity={
                "kind": "ollama",
                "host": "localhost",
                "port": 11434,
                "model_ref": model_ref,
            },
            progress=tuple(progress),
        )

    def warmup(self, model_ref) -> WarmupResult:
        return WarmupResult(
            state=self.warmup_state,
            detail=f"stub warmup {self.warmup_state}",
            elapsed_seconds=0.25,
            raw_response={"model_ref": model_ref},
            provider_identity={
                "kind": "ollama",
                "host": "localhost",
                "port": 11434,
                "model_ref": model_ref,
            },
            metadata={"done_reason": "load"},
        )


_FIXED_SYSTEM = {
    "os": {"name": "macOS", "version": "14.5", "machine": "arm64"},
    "cpu": {"name": "Apple M3", "physical_cores": 8, "logical_cores": 8},
    "memory": {"total_bytes": 17179869184, "total_human": "16.0 GiB"},
    "gpus": [{"name": "Apple GPU", "vram_bytes": None}],
    "gpu_probe": {"status": "detected", "detail": "stub"},
}


class TestListCommand(unittest.TestCase):
    """CLI-00103 list / FUN-00104."""

    def test_list_all_returns_catalog_and_scorers(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            rc, out, _ = _run_cli(["list", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_SUCCESS)
        payload = json.loads(out)
        self.assertEqual(len(payload["task_profiles"]), 1)
        self.assertEqual(payload["task_profiles"][0]["name"], "qa-basic")
        self.assertEqual(payload["task_profiles"][0]["case_count"], 1)
        self.assertEqual(len(payload["model_candidates"]), 1)
        self.assertEqual(payload["model_candidates"][0]["name"], "stub")
        # SCR-00101..00107 すべてが scorer 一覧に含まれる
        for s in (
            "exact_match", "normalized_match", "regex_match", "contains",
            "json_valid", "length_within", "numeric_close",
        ):
            self.assertIn(s, payload["scorers"])

    def test_list_kind_filter(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            rc, out, _ = _run_cli(
                ["list", "--config-dir", str(cfg_dir), "--kind", "scorers"]
            )
        self.assertEqual(rc, EXIT_SUCCESS)
        payload = json.loads(out)
        self.assertIn("scorers", payload)
        self.assertNotIn("task_profiles", payload)

    def test_list_invalid_config_dir_returns_configuration_error(self) -> None:
        rc, _, err = _run_cli(["list", "--config-dir", "/no/such/dir"])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("[error]", err)


class TestRunsCommand(unittest.TestCase):
    """CLI-00104 runs / FUN-00401."""

    def test_runs_empty_store(self) -> None:
        with TemporaryDirectory() as td:
            rc, out, _ = _run_cli(["runs", "--store-root", td])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertEqual(json.loads(out), [])

    def test_runs_lists_runs_and_meta(self) -> None:
        with TemporaryDirectory() as td:
            store_root = Path(td)
            run_dir = store_root / "run-test-1"
            run_dir.mkdir()
            (run_dir / "meta.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-test-1",
                        "started_at": "2026-01-01T00:00:00+00:00",
                        "model_candidate": {"name": "m"},
                        "task_profiles": ["tp1"],
                        "n_trials": 3,
                    }
                ),
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(["runs", "--store-root", str(store_root)])
        self.assertEqual(rc, EXIT_SUCCESS)
        rows = json.loads(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_id"], "run-test-1")
        self.assertEqual(rows[0]["model"], "m")
        self.assertEqual(rows[0]["n_trials"], 3)


class TestCheckCommand(unittest.TestCase):
    """CLI-00105 check / FUN-00105 / FUN-00402 / CFG-00501..00506."""

    def test_check_clean_config_success(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            rc, out, _ = _run_cli(["check", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertIn("問題なし", out)

    def test_check_detects_unknown_provider(self) -> None:
        # CFG-00502
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            (cfg_dir / "model_candidates.toml").write_text(
                """
[[model_candidate]]
name = "stub"
provider_kind = "no-such-provider"
provider_model_ref = "x"
""",
                encoding="utf-8",
            )
            rc, out, err = _run_cli(["check", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-00502", out)

    def test_check_detects_missing_expected_output(self) -> None:
        # FUN-00105: 期待出力欠落
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            (cfg_dir / "task_profiles" / "qa.toml").write_text(
                """
[task_profile]
name = "qa-basic"
purpose = "qa"

[task_profile.scorer]
name = "exact_match"

[[task_profile.cases]]
name = "c1"
input = "1+1?"
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(["check", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-00501", out)

    def test_check_detects_unknown_scorer(self) -> None:
        # CFG-00503
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            (cfg_dir / "task_profiles" / "qa.toml").write_text(
                """
[task_profile]
name = "qa-basic"
purpose = "qa"

[task_profile.scorer]
name = "no_such_scorer"

[[task_profile.cases]]
name = "c1"
input = "x"
expected_output = "y"
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(["check", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-00503", out)

    def test_check_load_failure_treated_as_configuration_error(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = Path(td) / "cfg"
            cfg_dir.mkdir()
            # task_profiles/ ディレクトリ無し → ConfigurationError
            rc, out, _ = _run_cli(["check", "--config-dir", str(cfg_dir)])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-LOAD", out)

    def test_check_comparison_unknown_run_id(self) -> None:
        # CFG-00506: 存在しない Run 識別子を含む Comparison 設定
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            store_root = base / "results"
            store_root.mkdir()
            cmp_cfg = base / "cmp.toml"
            cmp_cfg.write_text(
                """
[comparison]
runs = ["run-A", "run-B"]
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(
                [
                    "check",
                    "--config-dir", str(cfg_dir),
                    "--store-root", str(store_root),
                    "--comparison-config", str(cmp_cfg),
                ]
            )
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-00506", out)


class TestConfigLintCommand(unittest.TestCase):
    """CLI-00110 config lint / FUN-00406 / NFR-00302."""

    def test_config_lint_accepts_config_dir(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_valid_cfg(Path(td))
            rc, out, _ = _run_cli(["config", "lint", str(cfg_dir)])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertIn("問題なし", out)


class TestConfigDryRunCommand(unittest.TestCase):
    """CLI-00111 config dry-run / FUN-00407 / CLI-00308."""

    def test_config_dry_run_json_has_four_sections(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            run_cfg = cfg_dir / "run.toml"
            run_cfg.write_text(
                """
[run]
model_candidate = "stub"
task_profiles = ["qa-basic"]
n_trials = 1
""",
                encoding="utf-8",
            )
            with patch(
                "local_llm_benchmark.preflight.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli(["config", "dry-run", str(run_cfg)])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(
            set(payload.keys()),
            {"run", "probe", "prompt_check", "summary"},
        )
        self.assertEqual(payload["probe"]["provider_status"], "reachable")
        self.assertEqual(payload["probe"]["model_status"], "available")
        self.assertEqual(payload["prompt_check"]["status"], "ready")
        self.assertEqual(payload["summary"]["run_readiness"], "ready")

    def test_config_dry_run_markdown_output_has_four_sections(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            run_cfg = cfg_dir / "run.toml"
            run_cfg.write_text(
                """
[run]
model_candidate = "stub"
task_profiles = ["qa-basic"]
n_trials = 1
""",
                encoding="utf-8",
            )
            with patch(
                "local_llm_benchmark.preflight.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, _ = _run_cli(
                    ["config", "dry-run", str(run_cfg), "--format", "markdown"]
                )
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertLess(out.index("## run"), out.index("## probe"))
        self.assertLess(out.index("## probe"), out.index("## prompt_check"))
        self.assertLess(out.index("## prompt_check"), out.index("## summary"))

    def test_config_dry_run_negative_exit_code(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            run_cfg = cfg_dir / "run.toml"
            run_cfg.write_text(
                """
[run]
model_candidate = "stub"
task_profiles = ["qa-basic"]
n_trials = 1
""",
                encoding="utf-8",
            )
            with patch(
                "local_llm_benchmark.preflight.build_adapter",
                return_value=_StubProbeAdapter(model_status=MODEL_MISSING),
            ):
                rc, out, err = _run_cli(["config", "dry-run", str(run_cfg)])
        self.assertEqual(rc, EXIT_DRY_RUN_NEGATIVE)
        payload = json.loads(out)
        self.assertEqual(payload["summary"]["run_readiness"], "not_ready")
        self.assertIn("[config dry-run] model stub:tiny: missing", err)

    def test_config_dry_run_detects_prompt_issue(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            (cfg_dir / "task_profiles" / "qa.toml").write_text(
                """
[task_profile]
name = "qa-basic"
purpose = "qa"

[task_profile.scorer]
name = "exact_match"

[[task_profile.cases]]
name = "c1"
input = ""
expected_output = "2"
""",
                encoding="utf-8",
            )
            run_cfg = cfg_dir / "run.toml"
            run_cfg.write_text(
                """
[run]
model_candidate = "stub"
task_profiles = ["qa-basic"]
n_trials = 1
""",
                encoding="utf-8",
            )
            with patch(
                "local_llm_benchmark.preflight.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli(["config", "dry-run", str(run_cfg)])
        self.assertEqual(rc, EXIT_DRY_RUN_NEGATIVE)
        payload = json.loads(out)
        self.assertEqual(payload["prompt_check"]["status"], "invalid")
        self.assertIn(
            "[config dry-run] prompt_check qa-basic/c1: invalid",
            err,
        )

    def test_config_lint_run_file_uses_standard_support_sources(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir = _materialize_valid_cfg(base)
            run_cfg = cfg_dir / "run.toml"
            run_cfg.write_text(
                """
[run]
model_candidate = "stub"
task_profiles = ["qa-basic"]
n_trials = 1
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(["config", "lint", str(run_cfg)])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertIn("問題なし", out)

    def test_config_lint_model_candidates_need_support(self) -> None:
        with TemporaryDirectory() as td:
            target = Path(td) / "model_candidates.toml"
            target.write_text(
                """
[[model_candidate]]
name = "stub"
provider_kind = "ollama"
provider_model_ref = "stub:tiny"
""",
                encoding="utf-8",
            )
            rc, out, err = _run_cli(["config", "lint", str(target)])
        self.assertEqual(rc, EXIT_CONFIGURATION_ERROR)
        self.assertIn("CFG-LOAD", out)
        self.assertIn("補助設定ソース", out)
        self.assertIn("問題件数: 1", err)

    def test_config_lint_comparison_file_uses_store_root(self) -> None:
        with TemporaryDirectory() as td:
            base = Path(td)
            store_root = base / "results"
            for run_id in ("run-A", "run-B"):
                run_dir = store_root / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "meta.json").write_text(
                    json.dumps({"task_profiles": ["qa-basic"]}),
                    encoding="utf-8",
                )
            cmp_cfg = base / "comparison.toml"
            cmp_cfg.write_text(
                f"""
[comparison]
runs = ["run-A", "run-B"]
store_root = "{store_root}"
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(["config", "lint", str(cmp_cfg)])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertIn("問題なし", out)


class TestSystemProbeCommand(unittest.TestCase):
    """CLI-00109 / FUN-00404 / FUN-00405 / CLI-00307."""

    def test_system_probe_json_uses_provider_and_model_configs(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.system_probe.collect_system_snapshot",
                return_value=_FIXED_SYSTEM,
            ), patch(
                "local_llm_benchmark.system_probe.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli([
                    "system-probe", "--config-dir", str(cfg_dir),
                ])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(
            set(payload.keys()),
            {"system", "providers", "model_candidates", "summary"},
        )
        self.assertEqual(payload["providers"][0]["status"], "reachable")
        self.assertEqual(payload["model_candidates"][0]["status"], "available")
        self.assertFalse(payload["summary"]["probe_negative"])

    def test_system_probe_markdown_output_has_four_sections(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.system_probe.collect_system_snapshot",
                return_value=_FIXED_SYSTEM,
            ), patch(
                "local_llm_benchmark.system_probe.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, _ = _run_cli([
                    "system-probe", "--config-dir", str(cfg_dir),
                    "--format", "markdown",
                ])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertLess(out.index("## system"), out.index("## providers"))
        self.assertLess(
            out.index("## providers"),
            out.index("## model_candidates"),
        )
        self.assertLess(
            out.index("## model_candidates"),
            out.index("## summary"),
        )

    def test_system_probe_negative_exit_code(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.system_probe.collect_system_snapshot",
                return_value=_FIXED_SYSTEM,
            ), patch(
                "local_llm_benchmark.system_probe.build_adapter",
                return_value=_StubProbeAdapter(model_status=MODEL_MISSING),
            ):
                rc, out, err = _run_cli([
                    "system-probe", "--config-dir", str(cfg_dir),
                ])
        self.assertEqual(rc, EXIT_PROBE_NEGATIVE)
        payload = json.loads(out)
        self.assertTrue(payload["summary"]["probe_negative"])
        self.assertIn("[system-probe] model stub (stub:tiny): missing", err)


class TestProviderPreparationCommands(unittest.TestCase):
    """CLI-00112 / CLI-00113 / CLI-00114 / FUN-00408..00410."""

    def test_provider_status_json(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.provider_preparation.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli([
                    "provider", "status", "--config-dir", str(cfg_dir),
                ])
        self.assertEqual(rc, EXIT_SUCCESS)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(set(payload.keys()), {"providers", "summary"})
        self.assertEqual(payload["providers"][0]["status"], "reachable")
        self.assertFalse(payload["summary"]["provider_status_negative"])

    def test_provider_status_negative_exit_code(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.provider_preparation.build_adapter",
                return_value=_StubProbeAdapter(provider_status=PROBE_UNKNOWN),
            ):
                rc, out, err = _run_cli([
                    "provider", "status", "--config-dir", str(cfg_dir),
                ])
        self.assertEqual(rc, EXIT_PROVIDER_STATUS_NEGATIVE)
        payload = json.loads(out)
        self.assertTrue(payload["summary"]["provider_status_negative"])
        self.assertIn(
            "[provider status] provider ollama@localhost:11434: unknown",
            err,
        )

    def test_model_pull_json_and_progress(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.provider_preparation.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli([
                    "model", "pull", "--config-dir", str(cfg_dir),
                    "--model-candidate", "stub",
                ])
        self.assertEqual(rc, EXIT_SUCCESS)
        payload = json.loads(out)
        self.assertEqual(set(payload.keys()), {"target", "pull", "summary"})
        self.assertEqual(payload["pull"]["state"], "succeeded")
        self.assertIn("[model pull] 開始:", err)
        self.assertIn("[model pull] pulling manifest", err)
        self.assertIn("[model pull] 完了: state=succeeded", err)

    def test_model_warmup_json(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.provider_preparation.build_adapter",
                return_value=_StubProbeAdapter(),
            ):
                rc, out, err = _run_cli([
                    "model", "warmup", "--config-dir", str(cfg_dir),
                    "--model-candidate", "stub",
                ])
        self.assertEqual(rc, EXIT_SUCCESS)
        payload = json.loads(out)
        self.assertEqual(set(payload.keys()), {"target", "warmup", "summary"})
        self.assertEqual(payload["warmup"]["state"], "ready")
        self.assertIn("[model warmup] 開始:", err)
        self.assertIn("[model warmup] 完了: state=ready", err)

    def test_model_warmup_failure_is_runtime_error(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir = _materialize_probe_cfg(Path(td))
            with patch(
                "local_llm_benchmark.provider_preparation.build_adapter",
                return_value=_StubProbeAdapter(warmup_state="failed"),
            ):
                rc, out, err = _run_cli([
                    "model", "warmup", "--config-dir", str(cfg_dir),
                    "--model-ref", "stub:tiny",
                ])
        self.assertEqual(rc, EXIT_RUNTIME_ERROR)
        payload = json.loads(out)
        self.assertEqual(payload["warmup"]["state"], "failed")
        self.assertIn("[model warmup] 完了: state=failed", err)


class TestExitCodeUserInputError(unittest.TestCase):
    """CLI-00302: argparse 経由のユーザー入力誤りを正規化する."""

    def test_unknown_subcommand(self) -> None:
        rc, _, _ = _run_cli(["no-such-command"])
        self.assertEqual(rc, EXIT_USER_INPUT_ERROR)

    def test_missing_required_argument(self) -> None:
        rc, _, _ = _run_cli(["run"])
        self.assertEqual(rc, EXIT_USER_INPUT_ERROR)

    def test_invalid_choice(self) -> None:
        rc, _, _ = _run_cli(
            [
                "compare",
                "--store-root", "/tmp",
                "--axis", "bogus",
                "--run-id", "a", "--run-id", "b",
            ]
        )
        self.assertEqual(rc, EXIT_USER_INPUT_ERROR)

    def test_help_returns_success(self) -> None:
        rc, _, _ = _run_cli(["--help"])
        self.assertEqual(rc, EXIT_SUCCESS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
