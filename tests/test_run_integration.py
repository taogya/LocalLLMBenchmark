"""Run Coordinator + CLI 結合テスト.

対応 ID: FUN-00207 (1 Run = 1 Model × n Trial 完走), FUN-00204 (失敗継続),
        FUN-00206 (Run 識別子で参照可), NFR-00302 (標準ライブラリのみ)

Provider Adapter をモック実装に差し替えて run コマンドを完走させる。
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
    GenerationConditions,
    InferenceRequest,
    InferenceResponse,
    ModelCandidate,
    ProviderEndpoint,
    RunPlan,
    TaskProfile,
    Case,
    ScorerSpec,
)
from local_llm_benchmark.orchestration import RunCoordinator
from local_llm_benchmark.storage import ResultStore


# ---- モック Provider --------------------------------------------------------


@dataclass
class _StubAdapter:
    """成功シナリオ用: 期待出力をそのまま返す."""

    expected_text: str = "2"
    counter: int = 0

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        self.counter += 1
        return InferenceResponse(
            response_text=self.expected_text,
            elapsed_seconds=0.01 * self.counter,
            input_tokens=4,
            output_tokens=2,
            raw_response={"response": self.expected_text, "stub": True},
            provider_identity={
                "kind": "stub",
                "model_ref": request.model_ref,
            },
        )


@dataclass
class _PartialFailingAdapter:
    """偶数 trial のみ失敗を返す."""

    expected_text: str = "2"
    counter: int = 0

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        self.counter += 1
        if self.counter % 2 == 0:
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=0.001,
                input_tokens=None,
                output_tokens=None,
                raw_response={"error": "boom"},
                provider_identity={"kind": "stub", "model_ref": request.model_ref},
                failure_kind="provider_runtime_error",
                failure_detail="boom",
            )
        return InferenceResponse(
            response_text=self.expected_text,
            elapsed_seconds=0.01,
            input_tokens=4,
            output_tokens=2,
            raw_response={"response": self.expected_text},
            provider_identity={"kind": "stub", "model_ref": request.model_ref},
        )


def _build_plan() -> RunPlan:
    return RunPlan(
        model_candidate=ModelCandidate(
            name="stub-model",
            provider_kind="stub",
            provider_model_ref="stub:tiny",
        ),
        task_profiles=(
            TaskProfile(
                name="qa",
                purpose="qa",
                scorer=ScorerSpec(name="exact_match", args={}),
                cases=(Case(name="c1", input_text="1+1?", expected_output="2"),),
            ),
        ),
        n_trials=3,
        conditions=GenerationConditions(temperature=0.0, seed=42, max_tokens=16),
        provider_endpoint=ProviderEndpoint(kind="stub"),
    )


# ---- Coordinator 単体テスト ------------------------------------------------


class TestRunCoordinator(unittest.TestCase):
    def test_run_completes_three_trials(self) -> None:
        """FUN-00207 + FUN-00202: n=3 が完走し Run 識別子・ディレクトリが返る."""
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            coord = RunCoordinator(
                store=store,
                adapter_factory=lambda _plan: _StubAdapter(),
            )
            events: list[dict] = []
            result = coord.execute(_build_plan(), on_event=events.append)
            self.assertFalse(result.aborted)
            self.assertEqual(result.summary.success_trials, 3)
            self.assertEqual(result.summary.failure_trials, 0)
            self.assertEqual(result.summary.score_mean, 1.0)
            # FUN-00206: 識別子からディレクトリを引ける
            run_dir = Path(result.run_dir)
            self.assertTrue(run_dir.is_dir())
            self.assertTrue((run_dir / "meta.json").is_file())
            # 進捗イベントが流れる (NFR-00501)
            kinds = [e["type"] for e in events]
            self.assertIn("run_started", kinds)
            self.assertEqual(kinds.count("trial_completed"), 3)
            self.assertIn("run_completed", kinds)

    def test_partial_failure_is_recorded_and_continues(self) -> None:
        """FUN-00204 / SCR-00501: 個別失敗で停止せず母数から除外される."""
        with TemporaryDirectory() as td:
            store = ResultStore(Path(td))
            coord = RunCoordinator(
                store=store,
                adapter_factory=lambda _plan: _PartialFailingAdapter(),
            )
            result = coord.execute(_build_plan())
            self.assertFalse(result.aborted)
            self.assertEqual(result.summary.success_trials, 2)
            self.assertEqual(result.summary.failure_trials, 1)


# ---- CLI 結合テスト --------------------------------------------------------


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


class TestCLIRun(unittest.TestCase):
    """`run` サブコマンドが完走することを確認する.

    Provider はテスト中に差し替えるため、`build_adapter` をパッチする。
    """

    def _materialize(self, td: Path) -> tuple[Path, Path, Path]:
        cfg_dir = td / "configs"
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
expected_output = "2"
""",
        )
        _write(
            cfg_dir / "model_candidates.toml",
            """
[[model_candidate]]
name = "stub-model"
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
            """
[run]
model_candidate = "stub-model"
task_profiles = ["qa-basic"]
n_trials = 3

[run.generation]
temperature = 0.0
seed = 42
""",
        )
        return cfg_dir, run_cfg, results

    def test_cli_run_smoke(self) -> None:
        with TemporaryDirectory() as td:
            cfg_dir, run_cfg, results = self._materialize(Path(td))
            stub = _StubAdapter()
            stdout = io.StringIO()
            stderr = io.StringIO()
            # Coordinator が build_adapter を呼ぶので、そこを差し替える
            with patch(
                "local_llm_benchmark.orchestration.coordinator.build_adapter",
                return_value=stub,
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    rc = main(
                        [
                            "run",
                            "--config-dir",
                            str(cfg_dir),
                            "--run-config",
                            str(run_cfg),
                            "--store-root",
                            str(results),
                        ]
                    )
            self.assertEqual(rc, 0, msg=f"stderr=\n{stderr.getvalue()}")
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["model"], "stub-model")
            self.assertEqual(payload["n_trials"], 3)
            self.assertEqual(payload["summary"]["success_trials"], 3)
            self.assertFalse(payload["aborted"])
            run_dir = Path(payload["run_dir"])
            self.assertTrue(run_dir.is_dir())
            # NFR-00501: 進捗が標準エラーに出ている
            self.assertIn("[trial]", stderr.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
