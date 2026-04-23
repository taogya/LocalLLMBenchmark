"""Run 設定の dry-run preflight (
TASK-00013-02, COMP-00001 / COMP-00005 / COMP-00007).

`config dry-run` は run 設定を起点に、provider probe と代表 1 Case の
request 組立可否だけを確認する。実推論、採点、Result Store 書込、host facts
収集は行わない。
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from .config import (
    ConfigurationError,
    assemble_run_plan,
    load_run_config,
    load_support_bundle,
)
from .models import Case, RunPlan, TaskProfile
from .orchestration.coordinator import build_inference_request
from .providers import (
    MODEL_AVAILABLE,
    MODEL_UNKNOWN,
    PROBE_REACHABLE,
    PROBE_UNKNOWN,
    build_adapter,
)
from .providers.base import ModelProbeResult, ProviderProbeResult


def _pick_representative_case(plan: RunPlan) -> tuple[TaskProfile, Case]:
    if not plan.task_profiles:
        raise ConfigurationError("Run 設定から Task Profile を解決できない")
    task_profile = plan.task_profiles[0]
    if not task_profile.cases:
        raise ConfigurationError(
            f"Task Profile に Case が無い: {task_profile.name}"
        )
    return task_profile, task_profile.cases[0]


def _provider_identity(plan: RunPlan) -> dict[str, object]:
    return {
        "kind": plan.provider_endpoint.kind,
        "host": plan.provider_endpoint.host,
        "port": plan.provider_endpoint.port,
        "model_ref": plan.model_candidate.provider_model_ref,
    }


def _unknown_provider_probe(plan: RunPlan, detail: str) -> ProviderProbeResult:
    return ProviderProbeResult(
        status=PROBE_UNKNOWN,
        detail=detail,
        raw_response={"error": detail},
        provider_identity=_provider_identity(plan),
    )


def _unknown_model_probe(plan: RunPlan, detail: str) -> ModelProbeResult:
    return ModelProbeResult(
        model_ref=plan.model_candidate.provider_model_ref,
        status=MODEL_UNKNOWN,
        detail=detail,
        raw_response={"error": detail},
        provider_identity=_provider_identity(plan),
    )


def run_config_dry_run(
    run_config_path: Path,
    *,
    config_dir: Path | None = None,
    task_profile_dir: Path | None = None,
    model_candidates_path: Path | None = None,
    providers_path: Path | None = None,
    adapter_factory: Callable[[object], object] | None = None,
) -> dict[str, object]:
    """Run 設定起点の preflight 結果を JSON 正準形で返す."""
    if adapter_factory is None:
        adapter_factory = build_adapter

    run_config = load_run_config(run_config_path)
    bundle = load_support_bundle(
        run_config_path,
        config_dir=config_dir,
        task_profile_dir=task_profile_dir,
        model_candidates_path=model_candidates_path,
        providers_path=providers_path,
    )
    plan = assemble_run_plan(
        run_config=run_config,
        catalog=bundle.catalog,
        models=bundle.models,
        providers=bundle.providers,
    )
    task_profile, case = _pick_representative_case(plan)
    request = build_inference_request(
        plan,
        run_id="config-dry-run",
        task_profile_name=task_profile.name,
        case_name=case.name,
        case_input=case.input_text,
        sequence=1,
    )

    adapter = None
    try:
        adapter = adapter_factory(plan.provider_endpoint)
    except Exception as exc:
        provider_probe = _unknown_provider_probe(plan, f"adapter 初期化失敗: {exc}")
        model_probe = _unknown_model_probe(plan, f"adapter 初期化失敗: {exc}")
    else:
        try:
            provider_probe, model_probes = adapter.probe([request.model_ref])
        except Exception as exc:
            detail = f"provider probe 失敗: {exc}"
            provider_probe = _unknown_provider_probe(plan, detail)
            model_probe = _unknown_model_probe(plan, detail)
        else:
            model_probe = model_probes.get(request.model_ref)
            if model_probe is None:
                model_probe = _unknown_model_probe(
                    plan,
                    "adapter が model ref の判定結果を返さなかった",
                )

    prompt_status = "ready"
    prompt_detail = "representative case の prompt を組み立てられる"
    if not request.prompt:
        prompt_status = "invalid"
        prompt_detail = "prompt が空"
    else:
        validator = getattr(adapter, "validate_request", None)
        if callable(validator):
            validation_detail = validator(request)
            if validation_detail is not None:
                prompt_status = "invalid"
                prompt_detail = validation_detail

    blocking_issues: list[dict[str, str]] = []
    if provider_probe.status != PROBE_REACHABLE:
        blocking_issues.append(
            {"kind": "provider", "detail": provider_probe.detail}
        )
    if model_probe.status != MODEL_AVAILABLE:
        blocking_issues.append({"kind": "model", "detail": model_probe.detail})
    if prompt_status != "ready":
        blocking_issues.append(
            {"kind": "prompt_check", "detail": prompt_detail}
        )

    run_readiness = "ready" if not blocking_issues else "not_ready"
    return {
        "run": {
            "config_source_root": str(bundle.source_root),
            "run_config": str(run_config_path),
            "model_candidate": {
                "name": plan.model_candidate.name,
                "provider_kind": plan.model_candidate.provider_kind,
                "provider_model_ref": plan.model_candidate.provider_model_ref,
                "label": plan.model_candidate.label,
            },
            "task_profiles": [tp.name for tp in plan.task_profiles],
            "n_trials": plan.n_trials,
            "representative_case": {
                "task_profile": task_profile.name,
                "case": case.name,
            },
        },
        "probe": {
            "provider_identity": dict(provider_probe.provider_identity),
            "provider_status": provider_probe.status,
            "provider_evidence": provider_probe.detail,
            "model_ref": request.model_ref,
            "model_status": model_probe.status,
            "model_evidence": model_probe.detail,
        },
        "prompt_check": {
            "task_profile": task_profile.name,
            "case": case.name,
            "status": prompt_status,
            "detail": prompt_detail,
            "request_payload": {
                "model_ref": request.model_ref,
                "timeout_seconds": request.timeout_seconds,
                "prompt_chars": len(request.prompt),
                "generation": {
                    "temperature": request.generation.temperature,
                    "seed": request.generation.seed,
                    "max_tokens": request.generation.max_tokens,
                },
            },
        },
        "summary": {
            "blocking_issue_count": len(blocking_issues),
            "blocking_issues": blocking_issues,
            "run_readiness": run_readiness,
            "next_action": (
                "run"
                if run_readiness == "ready"
                else "fix_and_rerun_dry_run"
            ),
        },
    }


def render_config_dry_run_markdown(payload: Mapping[str, object]) -> str:
    """config dry-run の人間可読表示を生成する."""
    run = payload.get("run") or {}
    probe = payload.get("probe") or {}
    prompt_check = payload.get("prompt_check") or {}
    summary = payload.get("summary") or {}
    model = run.get("model_candidate") or {}
    representative_case = run.get("representative_case") or {}
    provider_identity = probe.get("provider_identity") or {}
    request_payload = prompt_check.get("request_payload") or {}
    generation = request_payload.get("generation") or {}

    provider_text = (
        f"{provider_identity.get('kind', 'unknown')}@"
        f"{provider_identity.get('host', '-')}"
        f":{provider_identity.get('port', '-')}"
    )
    lines = ["# config dry-run", "", "## run"]
    lines.append(f"- Run config: {run.get('run_config', 'unknown')}")
    lines.append(f"- Model candidate: {model.get('name', 'unknown')}")
    lines.append(
        "- Task profiles: "
        f"{', '.join(run.get('task_profiles') or []) or 'unknown'}"
    )
    lines.append(
        "- Representative case: "
        f"{representative_case.get('task_profile', 'unknown')}"
        f"/{representative_case.get('case', 'unknown')}"
    )

    lines.extend(["", "## probe"])
    lines.append(f"- Provider: {provider_text}")
    lines.append(
        f"- Provider status: {probe.get('provider_status', 'unknown')}"
    )
    lines.append(f"- Model status: {probe.get('model_status', 'unknown')}")
    lines.append(f"- Evidence: {probe.get('provider_evidence', '')}")
    lines.append(f"- Model evidence: {probe.get('model_evidence', '')}")

    lines.extend(["", "## prompt_check"])
    lines.append(f"- Status: {prompt_check.get('status', 'unknown')}")
    lines.append(f"- Detail: {prompt_check.get('detail', '')}")
    lines.append(
        "- Request payload: "
        f"model={request_payload.get('model_ref', 'unknown')}, "
        f"prompt_chars={request_payload.get('prompt_chars', 'unknown')}, "
        "timeout_seconds="
        f"{request_payload.get('timeout_seconds', 'unknown')}, "
        f"generation={generation}"
    )

    lines.extend(["", "## summary"])
    lines.append(
        f"- Blocking issue count: {summary.get('blocking_issue_count', 0)}"
    )
    lines.append(f"- Run readiness: {summary.get('run_readiness', 'unknown')}")
    lines.append(f"- Next action: {summary.get('next_action', 'unknown')}")
    for issue in summary.get('blocking_issues') or []:
        if not isinstance(issue, dict):
            continue
        lines.append(
            f"- Issue[{issue.get('kind', 'unknown')}]: "
            f"{issue.get('detail', '')}"
        )
    return "\n".join(lines) + "\n"


def emit_dry_run_issues(payload: Mapping[str, object]) -> list[str]:
    """dry-run-negative 判定につながる項目を 1 行 1 件で返す."""
    probe = payload.get("probe") or {}
    prompt_check = payload.get("prompt_check") or {}
    provider_identity = probe.get("provider_identity") or {}
    provider_text = (
        f"{provider_identity.get('kind', 'unknown')}@"
        f"{provider_identity.get('host', '-')}"
        f":{provider_identity.get('port', '-')}"
    )

    issues: list[str] = []
    if probe.get("provider_status") != PROBE_REACHABLE:
        issues.append(
            "[config dry-run] provider "
            f"{provider_text}: {probe.get('provider_status', PROBE_UNKNOWN)}"
            f" - {probe.get('provider_evidence', '')}"
        )
    if probe.get("model_status") != MODEL_AVAILABLE:
        issues.append(
            "[config dry-run] model "
            f"{probe.get('model_ref', 'unknown')}: "
            f"{probe.get('model_status', MODEL_UNKNOWN)}"
            f" - {probe.get('model_evidence', '')}"
        )
    if prompt_check.get("status") != "ready":
        issues.append(
            "[config dry-run] prompt_check "
            f"{prompt_check.get('task_profile', 'unknown')}"
            f"/{prompt_check.get('case', 'unknown')}: "
            f"{prompt_check.get('status', 'unknown')}"
            f" - {prompt_check.get('detail', '')}"
        )
    return issues
