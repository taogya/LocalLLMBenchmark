"""Comparison 設定 (CFG-00207) Loader のユニットテスト (TASK-00007-02).

対応 ID: CFG-00207, CFG-00506, DAT-00108, SCR-00806, SCR-00807, SCR-00808
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from local_llm_benchmark.config import (
    ConfigurationError,
    load_comparison_config,
)


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


class TestComparisonConfigLoader(unittest.TestCase):
    def test_minimal_two_runs(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "cmp.toml"
            _write(
                path,
                """
[comparison]
runs = ["run-A", "run-B"]
""",
            )
            cfg = load_comparison_config(path)
            self.assertEqual(cfg.run_ids, ("run-A", "run-B"))
            # SCR-00806/00807 既定値
            self.assertEqual(cfg.w_quality, 0.7)
            self.assertEqual(cfg.w_speed, 0.3)
            self.assertEqual(cfg.ranking_axis_default, "integrated")

    def test_dat_00108_requires_two_runs(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "cmp.toml"
            _write(
                path,
                """
[comparison]
runs = ["run-A"]
""",
            )
            with self.assertRaises(ConfigurationError):
                load_comparison_config(path)

    def test_weight_override(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "cmp.toml"
            _write(
                path,
                """
[comparison]
runs = ["run-A", "run-B"]
ranking_axis_default = "speed"

[comparison.weights]
w_quality = 0.4
w_speed = 0.6
""",
            )
            cfg = load_comparison_config(path)
            self.assertEqual(cfg.w_quality, 0.4)
            self.assertEqual(cfg.w_speed, 0.6)
            self.assertEqual(cfg.ranking_axis_default, "speed")

    def test_invalid_axis_rejected(self) -> None:
        with TemporaryDirectory() as td:
            path = Path(td) / "cmp.toml"
            _write(
                path,
                """
[comparison]
runs = ["run-A", "run-B"]
ranking_axis_default = "unknown"
""",
            )
            with self.assertRaises(ConfigurationError):
                load_comparison_config(path)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
