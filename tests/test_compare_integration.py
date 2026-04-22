"""run x2 -> compare -> report の結合テスト (TASK-00007-02).

対応 ID: FUN-00207, FUN-00308, FUN-00309, FUN-00310, FLW-00005, FLW-00006,
        CLI-00102, CLI-00106, CLI-00107, CLI-00108, NFR-00302
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from local_llm_benchmark.cli.main import main
from local_llm_benchmark.models import (
    InferenceRequest,
    InferenceResponse,
)


@dataclass
class _DeterministicAdapter:
    """モデル固有の応答テキストと latency を返す結合テスト用 stub."""

    response_text: str
    elapsed_seconds: float

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            response_text=self.response_text,
            elapsed_seconds=self.elapsed_seconds,
            input_tokens=4,
            output_tokens=2,
            raw_response={"response": self.response_text},
            provider_identity={"kind": "stub", "model_ref": request.model_ref},
        )


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _materialize_configs(td: Path) -> tuple[Path, Path, Path]:
    cfg_dir = td / "configs"
    results = td / "results"
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
name = "model-A"
provider_kind = "ollama"
provider_model_ref = "stub:A"

[[model_candidate]]
name = "model-B"
provider_kind = "ollama"
provider_model_ref = "stub:B"
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
    return cfg_dir, results, td


def _write_run_config(td: Path, model_name: str) -> Path:
    path = td / f"run-{model_name}.toml"
    _write(
        path,
        f"""
[run]
model_candidate = "{model_name}"
task_profiles = ["qa-basic"]
n_trials = 2

[run.generation]
temperature = 0.0
seed = 42
""",
    )
    return path


def _invoke(argv: list[str], adapter=None) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    if adapter is None:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = main(argv)
    else:
        with patch(
            "local_llm_benchmark.orchestration.coordinator.build_adapter",
            return_value=adapter,
        ):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                rc = main(argv)
    return rc, stdout.getvalue(), stderr.getvalue()


class TestRunCompareReportFlow(unittest.TestCase):
    def test_end_to_end(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir, results, td_path = _materialize_configs(Path(td))
            run_a_cfg = _write_run_config(td_path, "model-A")
            run_b_cfg = _write_run_config(td_path, "model-B")

            # ---- Run A: 高品質 (期待 "2" 一致) / 低速 ---------------------
            rc, out_a, _ = _invoke(
                [
                    "run", "--config-dir", str(cfg_dir),
                    "--run-config", str(run_a_cfg),
                    "--store-root", str(results),
                ],
                adapter=_DeterministicAdapter(response_text="2", elapsed_seconds=1.0),
            )
            self.assertEqual(rc, 0)
            run_a_id = json.loads(out_a)["run_id"]

            # ---- Run B: 低品質 (期待不一致) / 高速 ------------------------
            rc, out_b, _ = _invoke(
                [
                    "run", "--config-dir", str(cfg_dir),
                    "--run-config", str(run_b_cfg),
                    "--store-root", str(results),
                ],
                adapter=_DeterministicAdapter(response_text="0", elapsed_seconds=0.1),
            )
            # 期待不一致のみで失敗ではないので 0
            self.assertEqual(rc, 0)
            run_b_id = json.loads(out_b)["run_id"]
            self.assertNotEqual(run_a_id, run_b_id)

            # ---- compare -------------------------------------------------
            rc, out_cmp, err_cmp = _invoke(
                [
                    "compare",
                    "--store-root", str(results),
                    "--run-id", run_a_id,
                    "--run-id", run_b_id,
                ],
            )
            self.assertEqual(rc, 0, msg=err_cmp)
            cmp_payload = json.loads(out_cmp)
            cmp_id = cmp_payload["comparison_id"]
            self.assertTrue(cmp_id.startswith("cmp-"))
            self.assertEqual(set(cmp_payload["run_ids"]), {run_a_id, run_b_id})

            # ---- comparisons --------------------------------------------
            rc, out_list, _ = _invoke(
                ["comparisons", "--store-root", str(results)]
            )
            self.assertEqual(rc, 0)
            ids = [row["comparison_id"] for row in json.loads(out_list)]
            self.assertIn(cmp_id, ids)

            # ---- report (Comparison) ------------------------------------
            rc, md, _ = _invoke(
                [
                    "report",
                    "--store-root", str(results),
                    "--comparison-id", cmp_id,
                ],
            )
            self.assertEqual(rc, 0)
            # 3 軸ランキングが含まれる
            self.assertIn("品質重視", md)
            self.assertIn("速度重視", md)
            self.assertIn("統合", md)
            # 入力 Run 識別子が両方表示される
            self.assertIn(run_a_id, md)
            self.assertIn(run_b_id, md)

            # ---- report (Run) -------------------------------------------
            rc, md_run, _ = _invoke(
                [
                    "report",
                    "--store-root", str(results),
                    "--run-id", run_a_id,
                ],
            )
            self.assertEqual(rc, 0)
            self.assertIn("Run レポート", md_run)
            self.assertNotIn("ランキング", md_run)  # FLW-00002: ランキング非表示

    def test_compare_rejects_single_run(self) -> None:
        """DAT-00108 違反: --run-id 1 件のみは user-input error (CLI-00302)."""
        with TemporaryDirectory() as td:
            cfg_dir, results, td_path = _materialize_configs(Path(td))
            run_a_cfg = _write_run_config(td_path, "model-A")
            rc, out_a, _ = _invoke(
                [
                    "run", "--config-dir", str(cfg_dir),
                    "--run-config", str(run_a_cfg),
                    "--store-root", str(results),
                ],
                adapter=_DeterministicAdapter(response_text="2", elapsed_seconds=0.1),
            )
            self.assertEqual(rc, 0)
            run_a_id = json.loads(out_a)["run_id"]
            rc, _, err = _invoke(
                [
                    "compare", "--store-root", str(results),
                    "--run-id", run_a_id,
                ],
            )
            self.assertEqual(rc, 2)
            self.assertIn("DAT-00108", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
