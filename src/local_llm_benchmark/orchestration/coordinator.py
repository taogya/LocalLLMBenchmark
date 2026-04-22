"""Run Coordinator (TASK-00007-01, COMP-00010).

1 Run = 1 Model のオーケストレーションを担う (FUN-00207, ARCH-00207).

設計フローは FLW-00005 に準拠:
- 各 Trial で Provider Adapter -> (成功時のみ) Quality Scorer -> 進捗通知
- 個別 Trial 失敗は Run 全体を停止させない (FUN-00204, FLW-00101)
- Run 中断候補 (PVD-00301/00302/00306) は Coordinator が中断を判定する
  (本実装では「最初の発生で中断」の保守的方針)
- Run 完了時に Result Store へ集計値を保存する (FUN-00206, ARCH-00204)

進捗通知は標準エラー出力に書く責務を CLI 側に委ねるため、Coordinator は
コールバック (`on_event`) で抽象化する (NFR-00501)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .. import SCHEMA_VERSION
from ..models import (
    InferenceRequest,
    RunPlan,
    RunSummary,
    Trial,
)
from ..providers import RUN_ABORT_FAILURE_KINDS, ProviderAdapter, build_adapter
from ..scoring import SCORING_FAILURE_KIND, ScoreResult, get_scorer
from ..storage import ResultStore, generate_run_id
from .aggregator import aggregate_case, aggregate_run


ProgressEvent = Mapping[str, Any]
ProgressCallback = Callable[[ProgressEvent], None]


@dataclass(frozen=True)
class RunResult:
    """Coordinator の戻り値."""

    run_id: str
    run_dir: str
    summary: RunSummary
    aborted: bool
    abort_reason: str | None


@dataclass
class RunCoordinator:
    """Run の進行を司る単一の制御点 (COMP-00010)."""

    store: ResultStore
    adapter_factory: Callable[[RunPlan], ProviderAdapter] = field(
        default=lambda plan: build_adapter(plan.provider_endpoint)
    )

    def execute(
        self,
        plan: RunPlan,
        on_event: ProgressCallback | None = None,
        config_source_root: str | None = None,
    ) -> RunResult:
        emit = on_event or (lambda _ev: None)

        run_id = generate_run_id(plan.model_candidate.name)
        started_at = datetime.now(timezone.utc).isoformat()
        adapter = self.adapter_factory(plan)

        emit({"type": "run_started", "run_id": run_id})

        all_trials: list[Trial] = []
        aborted = False
        abort_reason: str | None = None

        # FLW-00005: 各 Task × 各 Case × n Trial を順に実行
        for tp in plan.task_profiles:
            scorer = get_scorer(tp.scorer.name)
            for case in tp.cases:
                for seq in range(1, plan.n_trials + 1):
                    trial = self._run_single_trial(
                        adapter=adapter,
                        plan=plan,
                        run_id=run_id,
                        task_profile_name=tp.name,
                        case_name=case.name,
                        case_input=case.input_text,
                        expected_output=case.expected_output,
                        sequence=seq,
                        scorer=scorer,
                        scorer_args=tp.scorer.args,
                    )
                    all_trials.append(trial)
                    emit(
                        {
                            "type": "trial_completed",
                            "run_id": run_id,
                            "task_profile": tp.name,
                            "case": case.name,
                            "trial": seq,
                            "n_trials": plan.n_trials,
                            "model": plan.model_candidate.name,
                            "failure_kind": trial.failure_kind,
                            "score": trial.quality_score,
                            "elapsed_seconds": trial.elapsed_seconds,
                        }
                    )
                    if (
                        trial.failure_kind is not None
                        and trial.failure_kind in RUN_ABORT_FAILURE_KINDS
                    ):
                        aborted = True
                        abort_reason = (
                            f"{trial.failure_kind}: {trial.failure_detail}"
                        )
                        emit(
                            {
                                "type": "run_aborted",
                                "run_id": run_id,
                                "reason": abort_reason,
                            }
                        )
                        break
                if aborted:
                    break
            if aborted:
                break

        # 集計: (task, case, model) でグルーピング
        aggregations = []
        groups: dict[tuple[str, str, str], list[Trial]] = {}
        for t in all_trials:
            groups.setdefault(
                (t.task_profile_name, t.case_name, t.model_name), []
            ).append(t)
        for key in sorted(groups):
            aggregations.append(aggregate_case(groups[key]))
        summary = aggregate_run(aggregations, plan.model_candidate.name)

        # provider 識別: 1 Run = 1 Model の前提で代表値を載せる (PVD-00208)
        provider_identity = {
            "kind": plan.provider_endpoint.kind,
            "host": plan.provider_endpoint.host,
            "port": plan.provider_endpoint.port,
            "model_ref": plan.model_candidate.provider_model_ref,
        }
        meta: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "started_at": started_at,
            "model_candidate": {
                "name": plan.model_candidate.name,
                "provider_kind": plan.model_candidate.provider_kind,
                "provider_model_ref": plan.model_candidate.provider_model_ref,
                "label": plan.model_candidate.label,
            },
            "task_profiles": [tp.name for tp in plan.task_profiles],
            "n_trials": plan.n_trials,
            # FUN-00203: 生成条件を Run メタとして保存
            "generation_conditions": {
                "temperature": plan.conditions.temperature,
                "seed": plan.conditions.seed,
                "max_tokens": plan.conditions.max_tokens,
            },
            "provider_identity": provider_identity,
            "config_source_root": config_source_root,  # CFG-00302
            "aborted": aborted,
            "abort_reason": abort_reason,
        }
        run_dir = self.store.write_run(
            run_id=run_id,
            meta=meta,
            trials=all_trials,
            aggregations=aggregations,
            run_summary=summary,
        )
        emit({"type": "run_completed", "run_id": run_id, "run_dir": str(run_dir)})
        return RunResult(
            run_id=run_id,
            run_dir=str(run_dir),
            summary=summary,
            aborted=aborted,
            abort_reason=abort_reason,
        )

    # ---- 内部 -----------------------------------------------------------

    def _run_single_trial(
        self,
        adapter: ProviderAdapter,
        plan: RunPlan,
        run_id: str,
        task_profile_name: str,
        case_name: str,
        case_input: str,
        expected_output: str | None,
        sequence: int,
        scorer,
        scorer_args: Mapping[str, Any],
    ) -> Trial:
        request = InferenceRequest(
            prompt=case_input,
            generation=plan.conditions,
            model_ref=plan.model_candidate.provider_model_ref,
            timeout_seconds=plan.provider_endpoint.timeout_seconds,
            run_id=run_id,
            task_profile_name=task_profile_name,
            case_name=case_name,
            trial_index=sequence,
        )
        response = adapter.infer(request)
        if response.failure_kind is not None:
            # FLW-00101: 失敗 Trial として記録、継続判定は呼び出し側
            return Trial(
                task_profile_name=task_profile_name,
                case_name=case_name,
                model_name=plan.model_candidate.name,
                sequence=sequence,
                response_text=None,
                elapsed_seconds=response.elapsed_seconds,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                quality_score=None,
                failure_kind=response.failure_kind,
                failure_detail=response.failure_detail,
            )
        # 成功時のみ採点 (FLW-00005)
        score: ScoreResult = scorer.score(
            response_text=response.response_text or "",
            expected_output=expected_output,
            args=scorer_args,
        )
        if score.failure_kind is not None:
            # PVD-00307 scoring 適用不可: Trial 失敗として記録、継続
            return Trial(
                task_profile_name=task_profile_name,
                case_name=case_name,
                model_name=plan.model_candidate.name,
                sequence=sequence,
                response_text=response.response_text,
                elapsed_seconds=response.elapsed_seconds,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                quality_score=None,
                failure_kind=score.failure_kind or SCORING_FAILURE_KIND,
                failure_detail=score.failure_detail,
            )
        return Trial(
            task_profile_name=task_profile_name,
            case_name=case_name,
            model_name=plan.model_candidate.name,
            sequence=sequence,
            response_text=response.response_text,
            elapsed_seconds=response.elapsed_seconds,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            quality_score=score.score,
            failure_kind=None,
            failure_detail=None,
        )
