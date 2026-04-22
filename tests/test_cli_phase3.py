"""CLI list / runs / check / 終了コードのテスト (TASK-00007-03).

対応 ID: CLI-00103, CLI-00104, CLI-00105, CLI-00301, CLI-00302, CLI-00303,
FUN-00104, FUN-00105, FUN-00401, FUN-00402, CFG-00501..00506
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from local_llm_benchmark.cli.main import (
    EXIT_CONFIGURATION_ERROR,
    EXIT_SUCCESS,
    EXIT_USER_INPUT_ERROR,
    main,
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


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


class TestListCommand(unittest.TestCase):
    """CLI-00103 list / FUN-00104."""

    def test_list_all_returns_task_profiles_and_models_and_scorers(self) -> None:
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
