"""Configuration Loader / Task Catalog のユニットテスト.

対応 ID: FUN-00101, FUN-00102, FUN-00105, FUN-00207, NFR-00302, CFG-00101..00107
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from local_llm_benchmark.config import (
    ConfigurationError,
    assemble_run_plan,
    load_config_bundle,
    load_run_config,
    load_task_catalog,
)


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _bundle_layout(root: Path) -> None:
    """最小整合の設定ディレクトリを作る."""
    _write(
        root / "task_profiles" / "qa.toml",
        """
[task_profile]
name = "qa-basic"
purpose = "短答 QA"

[task_profile.scorer]
name = "exact_match"
args = { normalize_whitespace = true }

[[task_profile.cases]]
name = "case-1"
input = "1+1?"
expected_output = "2"
""",
    )
    _write(
        root / "model_candidates.toml",
        """
[[model_candidate]]
name = "qwen2-1.5b"
provider_kind = "ollama"
provider_model_ref = "qwen2:1.5b"
""",
    )
    _write(
        root / "providers.toml",
        """
[[provider]]
kind = "ollama"
host = "localhost"
port = 11434
timeout_seconds = 60
""",
    )


class TestConfigBundle(unittest.TestCase):
    """COMP-00007 / COMP-00008 の最小整合読込."""

    def test_load_minimum_valid_bundle(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _bundle_layout(root)
            bundle = load_config_bundle(root)
            self.assertIn("qa-basic", bundle.catalog.profiles)
            self.assertIn("qwen2-1.5b", bundle.models)
            self.assertIn("ollama", bundle.providers)
            tp = bundle.catalog.profiles["qa-basic"]
            self.assertEqual(tp.scorer.name, "exact_match")
            self.assertEqual(len(tp.cases), 1)

    def test_task_profile_requires_at_least_one_case(self) -> None:
        """DAT-00101 を Loader 側で強制する."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root / "task_profiles" / "empty.toml",
                """
[task_profile]
name = "empty"
purpose = "x"
[task_profile.scorer]
name = "exact_match"
cases = []
""",
            )
            with self.assertRaises(ConfigurationError):
                load_task_catalog(root / "task_profiles")

    def test_provider_rejects_secret_keys(self) -> None:
        """CFG-00402: 平文の認証情報を拒否."""
        with TemporaryDirectory() as td:
            root = Path(td)
            _bundle_layout(root)
            _write(
                root / "providers.toml",
                """
[[provider]]
kind = "ollama"
api_key = "should-not-store-here"
""",
            )
            with self.assertRaises(ConfigurationError):
                load_config_bundle(root)


class TestRunConfigAndAssembly(unittest.TestCase):
    """CFG-00107 / FUN-00207 の検証."""

    def _write_run_cfg(self, p: Path, model: object = "qwen2-1.5b") -> None:
        if isinstance(model, list):
            model_line = f"model_candidate = {model!r}"
        else:
            model_line = f'model_candidate = "{model}"'
        _write(
            p,
            f"""
[run]
{model_line}
task_profiles = ["qa-basic"]
n_trials = 3

[run.generation]
temperature = 0.0
seed = 42
max_tokens = 64
""",
        )

    def test_run_config_one_model_only(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _bundle_layout(root)
            run_cfg_path = root / "run.toml"
            self._write_run_cfg(run_cfg_path)
            bundle = load_config_bundle(root)
            cfg = load_run_config(run_cfg_path)
            plan = assemble_run_plan(cfg, bundle.catalog, bundle.models, bundle.providers)
            self.assertEqual(plan.model_candidate.name, "qwen2-1.5b")
            self.assertEqual(plan.n_trials, 3)
            self.assertEqual(plan.conditions.seed, 42)

    def test_run_config_rejects_multiple_models(self) -> None:
        """FUN-00207 / CLI-00106: 複数 Model 指定はエラー."""
        with TemporaryDirectory() as td:
            run_cfg_path = Path(td) / "run.toml"
            self._write_run_cfg(run_cfg_path, model=["a", "b"])
            with self.assertRaises(ConfigurationError):
                load_run_config(run_cfg_path)

    def test_assemble_rejects_unknown_model(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _bundle_layout(root)
            run_cfg_path = root / "run.toml"
            self._write_run_cfg(run_cfg_path, model="nope")
            cfg = load_run_config(run_cfg_path)
            bundle = load_config_bundle(root)
            with self.assertRaises(ConfigurationError):
                assemble_run_plan(cfg, bundle.catalog, bundle.models, bundle.providers)

    def test_assemble_rejects_unknown_task_profile(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            _bundle_layout(root)
            run_cfg_path = root / "run.toml"
            _write(
                run_cfg_path,
                """
[run]
model_candidate = "qwen2-1.5b"
task_profiles = ["does-not-exist"]
n_trials = 1
""",
            )
            cfg = load_run_config(run_cfg_path)
            bundle = load_config_bundle(root)
            with self.assertRaises(ConfigurationError):
                assemble_run_plan(cfg, bundle.catalog, bundle.models, bundle.providers)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
