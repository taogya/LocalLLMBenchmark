"""v1.0.0 smoke 観点の e2e 検証 (TASK-00007-03).

`docs/development/release-criteria.md` の v1.0.0 smoke 観点チェックリストを
コードでカバーできる範囲を一通り通すテスト。Provider Adapter は stub に
差し替えて HTTP を行わない。

対応 ID: FUN-00104, FUN-00105, FUN-00202, FUN-00203, FUN-00204, FUN-00205,
        FUN-00206, FUN-00207, FUN-00305, FUN-00306, FUN-00307, FUN-00308,
        FUN-00309, FUN-00310, FUN-00401, FUN-00402, FUN-00403,
        NFR-00003, NFR-00004, NFR-00102, NFR-00103, NFR-00203, NFR-00204,
        NFR-00501, NFR-00502
"""

from __future__ import annotations

import io
import json
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from local_llm_benchmark.cli.main import (
    EXIT_PARTIAL_FAILURE,
    EXIT_SUCCESS,
    EXIT_USER_INPUT_ERROR,
    main,
)
from local_llm_benchmark.models import InferenceRequest, InferenceResponse


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@dataclass
class _StubAdapter:
    """期待出力をそのまま返す stub."""

    expected_text: str = "2"

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            response_text=self.expected_text,
            elapsed_seconds=0.01,
            input_tokens=4,
            output_tokens=2,
            raw_response={"response": self.expected_text, "stub": True},
            provider_identity={
                "kind": "stub",
                "host": "localhost",
                "port": 0,
                "model_ref": request.model_ref,
            },
        )


@dataclass
class _PartialFailingAdapter:
    """1 trial 目を失敗、その後成功を返す."""

    expected_text: str = "2"
    counter: int = 0

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        self.counter += 1
        if self.counter == 1:
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=0.001,
                input_tokens=None,
                output_tokens=None,
                raw_response={"error": "stub-failure"},
                provider_identity={
                    "kind": "stub", "host": "localhost", "port": 0,
                    "model_ref": request.model_ref,
                },
                failure_kind="provider_runtime_error",
                failure_detail="stub-failure",
            )
        return InferenceResponse(
            response_text=self.expected_text,
            elapsed_seconds=0.01,
            input_tokens=4,
            output_tokens=2,
            raw_response={"response": self.expected_text},
            provider_identity={
                "kind": "stub", "host": "localhost", "port": 0,
                "model_ref": request.model_ref,
            },
        )


def _materialize(td: Path, *, model_name: str = "stub-model",
                 expected: str = "2") -> tuple[Path, Path, Path]:
    """通常の Run 用設定一式を書き出す."""
    cfg_dir = td / "cfg"
    run_cfg = td / "run.toml"
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
expected_output = "%s"
""" % expected,
    )
    _write(
        cfg_dir / "model_candidates.toml",
        f"""
[[model_candidate]]
name = "{model_name}"
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
    _write(
        run_cfg,
        f"""
[run]
model_candidate = "{model_name}"
task_profiles = ["qa-basic"]
n_trials = 3

[run.generation]
temperature = 0.0
seed = 42
""",
    )
    return cfg_dir, run_cfg, results


def _run_cli(argv: list[str], adapter=None) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    if adapter is None:
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(argv)
    else:
        with patch(
            "local_llm_benchmark.orchestration.coordinator.build_adapter",
            return_value=adapter,
        ):
            with redirect_stdout(out), redirect_stderr(err):
                rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


class TestSmokeChecklist(unittest.TestCase):
    """v1.0.0 smoke 観点を 1 ケースで縦断する."""

    # ---- run + n_trials + 進捗 + provider 識別 + 結果ディレクトリ ---------

    def test_run_full_flow_and_metadata(self) -> None:
        """FUN-00207, FUN-00202 (n=3), FUN-00203, FUN-00206, FUN-00306,
        NFR-00102, NFR-00103, NFR-00204, NFR-00501.
        """
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = _materialize(Path(td))
            rc, out, err = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS, msg=err)
            payload = json.loads(out)
            run_dir = Path(payload["run_dir"])
            self.assertTrue(run_dir.is_dir())  # FUN-00206
            self.assertEqual(payload["n_trials"], 3)  # FUN-00202

            # NFR-00501: 進捗が標準エラーへ出ている
            self.assertIn("[trial]", err)

            # NFR-00103: 生応答と集計値が分離
            self.assertTrue((run_dir / "raw" / "trials.jsonl").is_file())
            self.assertTrue((run_dir / "aggregation.json").is_file())
            self.assertTrue((run_dir / "meta.json").is_file())

            meta = json.loads((run_dir / "meta.json").read_text("utf-8"))
            # NFR-00204 / DAT-00201
            self.assertIn("schema_version", meta)
            # FUN-00203: 生成条件
            self.assertEqual(meta["generation_conditions"]["temperature"], 0.0)
            self.assertEqual(meta["generation_conditions"]["seed"], 42)
            # FUN-00306 / NFR-00102: provider 識別
            self.assertEqual(meta["provider_identity"]["kind"], "ollama")
            self.assertIn("model_ref", meta["provider_identity"])

    def test_run_with_n_trials_one(self) -> None:
        """FUN-00202: n=1 と n=3 の両方が反映される (n=3 は前テストで担保)."""
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = _materialize(Path(td))
            run_cfg.write_text(
                """
[run]
model_candidate = "stub-model"
task_profiles = ["qa-basic"]
n_trials = 1

[run.generation]
temperature = 0.0
""",
                encoding="utf-8",
            )
            rc, out, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            self.assertEqual(json.loads(out)["n_trials"], 1)

    # ---- 失敗継続 + 失敗種別表示 -----------------------------------------

    def test_run_partial_failure_continues(self) -> None:
        """FUN-00204, FUN-00205, NFR-00003, NFR-00502, CLI-00305."""
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = _materialize(Path(td))
            rc, out, err = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_PartialFailingAdapter(),
            )
            self.assertEqual(rc, EXIT_PARTIAL_FAILURE)
            payload = json.loads(out)
            self.assertEqual(payload["summary"]["success_trials"], 2)  # n=3 中 2 成功
            self.assertEqual(payload["summary"]["failure_trials"], 1)
            # NFR-00003: 失敗種別 (PVD-) が標準エラーに出ている
            self.assertIn("FAIL(provider_runtime_error)", err)

            # NFR-00502: 失敗 Trial 情報 + 生応答がファイルに残る
            run_dir = Path(payload["run_dir"])
            jsonl = (run_dir / "raw" / "trials.jsonl").read_text("utf-8")
            self.assertIn("provider_runtime_error", jsonl)

    # ---- list / runs / report --------------------------------------------

    def test_list_runs_report_flow(self) -> None:
        """FUN-00104, FUN-00307, FUN-00401."""
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = _materialize(Path(td))
            # list (FUN-00104)
            rc, out, _ = _run_cli(["list", "--config-dir", str(cfg_dir)])
            self.assertEqual(rc, EXIT_SUCCESS)
            data = json.loads(out)
            self.assertEqual(data["task_profiles"][0]["name"], "qa-basic")
            self.assertEqual(data["model_candidates"][0]["name"], "stub-model")

            # run
            rc, out, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            run_id = json.loads(out)["run_id"]

            # runs (FUN-00401)
            rc, out, _ = _run_cli(["runs", "--store-root", str(results)])
            self.assertEqual(rc, EXIT_SUCCESS)
            rows = json.loads(out)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], run_id)

            # report (FUN-00307): ランキングが含まれない
            rc, out, _ = _run_cli(
                ["report", "--store-root", str(results), "--run-id", run_id]
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            self.assertIn("Run レポート", out)
            self.assertNotIn("ランキング", out)

    # ---- compare 全フロー -------------------------------------------------

    def test_compare_full_flow(self) -> None:
        """FUN-00305, FUN-00308, FUN-00310, FUN-00403, NFR-00004."""
        with TemporaryDirectory() as td:
            base = Path(td)
            cfg_dir, run_cfg, results = _materialize(base, model_name="m-A")
            # Run A
            rc, out_a, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            run_a = json.loads(out_a)["run_id"]

            # 設定を Model B に書き換えて Run B
            (cfg_dir / "model_candidates.toml").write_text(
                """
[[model_candidate]]
name = "m-B"
provider_kind = "ollama"
provider_model_ref = "stub:tiny2"
""",
                encoding="utf-8",
            )
            run_cfg.write_text(
                """
[run]
model_candidate = "m-B"
task_profiles = ["qa-basic"]
n_trials = 3

[run.generation]
temperature = 0.0
seed = 42
""",
                encoding="utf-8",
            )
            rc, out_b, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            run_b = json.loads(out_b)["run_id"]

            # compare (FUN-00308 / FUN-00310: 重み上書き)
            rc, out, _ = _run_cli(
                ["compare", "--store-root", str(results),
                 "--run-id", run_a, "--run-id", run_b,
                 "--w-quality", "0.6", "--w-speed", "0.4",
                 "--axis", "integrated"]
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            cmp_payload = json.loads(out)
            cmp_id = cmp_payload["comparison_id"]
            self.assertEqual(cmp_payload["weights"]["w_quality"], 0.6)

            # comparisons (FUN-00403)
            rc, out, _ = _run_cli(["comparisons", "--store-root", str(results)])
            self.assertEqual(rc, EXIT_SUCCESS)
            self.assertEqual(json.loads(out)[0]["comparison_id"], cmp_id)

            # report の Markdown / FUN-00305 (Markdown 派生形)
            rc, md_out, _ = _run_cli(
                ["report", "--store-root", str(results),
                 "--comparison-id", cmp_id]
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            # NFR-00004: 人間可読出力の先頭にランキング表が現れる
            # (タイトル直後にランキングが出ること)
            head = md_out.splitlines()[:6]
            self.assertTrue(any("ランキング" in line for line in head),
                            msg=f"ranking not at top: head={head!r}")
            self.assertIn("ランキング: 品質重視", md_out)
            self.assertIn("ランキング: 速度重視", md_out)
            self.assertIn("ランキング: 統合", md_out)

    # ---- DAT-00109 拒否 (FUN-00309) --------------------------------------

    def test_compare_rejects_single_run(self) -> None:
        """FUN-00309: Run 1 件のみ指定 (DAT-00108)."""
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = _materialize(Path(td))
            rc, out, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            run_id = json.loads(out)["run_id"]
            rc, _, err = _run_cli(
                ["compare", "--store-root", str(results), "--run-id", run_id]
            )
            self.assertEqual(rc, EXIT_USER_INPUT_ERROR)
            self.assertIn("DAT-00108", err)

    # ---- check 独立実行 (FUN-00402) --------------------------------------

    def test_check_runs_independently_of_run(self) -> None:
        """FUN-00402."""
        with TemporaryDirectory() as td:
            cfg_dir, _, results = _materialize(Path(td))
            results.mkdir()
            rc, out, _ = _run_cli(
                ["check", "--config-dir", str(cfg_dir),
                 "--store-root", str(results)]
            )
            self.assertEqual(rc, EXIT_SUCCESS)
            self.assertIn("問題なし", out)

    # ---- BYO 外部設定 (NFR-00203) ----------------------------------------

    def test_external_config_directory_works(self) -> None:
        """NFR-00203: ツール本体ディレクトリ外の設定で完走."""
        with TemporaryDirectory() as td:
            external = Path(td) / "byo"
            cfg_dir, run_cfg, results = _materialize(external)
            rc, _, _ = _run_cli(
                ["run", "--config-dir", str(cfg_dir),
                 "--run-config", str(run_cfg),
                 "--store-root", str(results)],
                adapter=_StubAdapter(),
            )
            self.assertEqual(rc, EXIT_SUCCESS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
