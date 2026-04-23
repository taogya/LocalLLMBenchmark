"""provider preparation CLI helpers (
TASK-00014-02, COMP-00001 / COMP-00005 / COMP-00007).

`provider status` は provider inventory の直接確認、`model pull` と
`model warmup` は explicit preparation を担う。host facts や Run 設定は
読まない。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .config import (
    ConfigurationError,
    load_model_candidates,
    load_provider_endpoints,
)
from .models import ProviderEndpoint
from .providers import PROBE_REACHABLE, PullProgress, build_adapter


@dataclass(frozen=True)
class ModelOperationTarget:
    """model pull / warmup で使う解決済み target."""

    provider_endpoint: ProviderEndpoint
    provider_kind: str
    model_ref: str
    requested_target: str
    model_candidate_name: str | None = None


def _endpoint_payload(endpoint: ProviderEndpoint) -> dict[str, object]:
    return {
        "host": endpoint.host,
        "port": endpoint.port,
        "timeout_seconds": endpoint.timeout_seconds,
    }


def _resolve_provider_endpoint(
    providers: Mapping[str, ProviderEndpoint],
    provider_kind: str | None,
) -> ProviderEndpoint:
    if provider_kind is None:
        if len(providers) == 1:
            return next(iter(providers.values()))
        raise ConfigurationError(
            "provider を一意に決定できないため --provider が必要"
        )
    endpoint = providers.get(provider_kind)
    if endpoint is None:
        raise ConfigurationError(f"未登録の provider 種別: {provider_kind}")
    return endpoint


def resolve_model_operation_target(
    config_dir: Path,
    *,
    provider_kind: str | None,
    model_candidate_name: str | None,
    model_ref: str | None,
) -> ModelOperationTarget:
    """config-dir から model pull / warmup 用 target を解決する."""
    if (model_candidate_name is None) == (model_ref is None):
        raise ConfigurationError(
            "--model-candidate または --model-ref のどちらか 1 つを指定する"
        )

    providers = load_provider_endpoints(config_dir / "providers.toml")
    if model_candidate_name is not None:
        models = load_model_candidates(config_dir / "model_candidates.toml")
        model = models.get(model_candidate_name)
        if model is None:
            raise ConfigurationError(
                f"未登録の Model Candidate を参照: {model_candidate_name}"
            )
        if provider_kind is not None and provider_kind != model.provider_kind:
            raise ConfigurationError(
                "--provider と --model-candidate の provider_kind が一致しない"
            )
        endpoint = _resolve_provider_endpoint(providers, model.provider_kind)
        return ModelOperationTarget(
            provider_endpoint=endpoint,
            provider_kind=model.provider_kind,
            model_ref=model.provider_model_ref,
            requested_target=model_candidate_name,
            model_candidate_name=model_candidate_name,
        )

    endpoint = _resolve_provider_endpoint(providers, provider_kind)
    assert model_ref is not None
    return ModelOperationTarget(
        provider_endpoint=endpoint,
        provider_kind=endpoint.kind,
        model_ref=model_ref,
        requested_target=model_ref,
    )


def run_provider_status(
    config_dir: Path,
    *,
    provider_kinds: Sequence[str] | None = None,
    adapter_factory: Callable[[ProviderEndpoint], object] | None = None,
) -> dict[str, object]:
    """provider status の JSON 正準形を返す."""
    if adapter_factory is None:
        adapter_factory = build_adapter
    providers = load_provider_endpoints(config_dir / "providers.toml")
    selected_kinds = sorted(provider_kinds or providers.keys())
    rows: list[dict[str, object]] = []
    for provider_kind in selected_kinds:
        endpoint = providers.get(provider_kind)
        if endpoint is None:
            raise ConfigurationError(f"未登録の provider 種別: {provider_kind}")
        try:
            adapter = adapter_factory(endpoint)
        except Exception as exc:
            raise ConfigurationError(
                f"provider adapter 構築失敗 ({provider_kind}): {exc}"
            ) from exc
        snapshot = adapter.status()
        inventory_models = []
        for item in snapshot.inventory:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if name is None:
                continue
            inventory_models.append(str(name))
        rows.append(
            {
                "provider_kind": provider_kind,
                "endpoint": _endpoint_payload(endpoint),
                "status": snapshot.status,
                "evidence": snapshot.detail,
                "version_info": dict(snapshot.version_info),
                "inventory": {
                    "count": len(inventory_models),
                    "models": inventory_models,
                },
            }
        )

    reachable_count = sum(
        1 for row in rows if row.get("status") == PROBE_REACHABLE
    )
    negative_count = len(rows) - reachable_count
    return {
        "providers": rows,
        "summary": {
            "reachable_count": reachable_count,
            "negative_count": negative_count,
            "provider_status_negative": negative_count > 0,
            "next_action": (
                "model_pull_or_warmup"
                if negative_count == 0
                else "fix_provider_and_retry"
            ),
        },
    }


def render_provider_status_markdown(payload: Mapping[str, object]) -> str:
    """provider status の Markdown 表示を生成する."""
    providers = payload.get("providers") or []
    summary = payload.get("summary") or {}

    lines = ["# provider status", "", "## providers"]
    if providers:
        lines.append(
            "| Provider | Endpoint | Status | Version | Inventory | Evidence |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in providers:
            if not isinstance(row, dict):
                continue
            endpoint = row.get("endpoint") or {}
            inventory = row.get("inventory") or {}
            version = row.get("version_info") or {}
            endpoint_text = (
                f"{endpoint.get('host', '-')}:{endpoint.get('port', '-')}"
                if isinstance(endpoint, dict)
                else "-"
            )
            lines.append(
                f"| {row.get('provider_kind', 'unknown')} | {endpoint_text} | "
                f"{row.get('status', 'unknown')} | "
                f"{version.get('version', 'unknown')} | "
                f"{inventory.get('count', 0)} | {row.get('evidence', '')} |"
            )
            models = (
                inventory.get("models")
                if isinstance(inventory, dict)
                else []
            )
            if models:
                lines.append(
                    f"- {row.get('provider_kind', 'unknown')} models: "
                    f"{', '.join(str(model) for model in models)}"
                )
    else:
        lines.append("- provider 定義なし")

    lines.extend(["", "## summary"])
    lines.append(f"- Reachable count: {summary.get('reachable_count', 0)}")
    lines.append(f"- Negative count: {summary.get('negative_count', 0)}")
    lines.append(
        "- Provider status negative: "
        f"{'yes' if summary.get('provider_status_negative') else 'no'}"
    )
    lines.append(f"- Next action: {summary.get('next_action', 'unknown')}")
    return "\n".join(lines) + "\n"


def emit_provider_status_issues(payload: Mapping[str, object]) -> list[str]:
    """provider-status-negative 判定につながる項目を 1 行 1 件で返す."""
    issues: list[str] = []
    for row in payload.get("providers") or []:
        if not isinstance(row, dict) or row.get("status") == PROBE_REACHABLE:
            continue
        endpoint = row.get("endpoint") or {}
        endpoint_text = (
            f"{endpoint.get('host', '-')}:{endpoint.get('port', '-')}"
            if isinstance(endpoint, dict)
            else "-"
        )
        issues.append(
            "[provider status] provider "
            f"{row.get('provider_kind', 'unknown')}@{endpoint_text}: "
            f"{row.get('status', 'unknown')} - {row.get('evidence', '')}"
        )
    return issues


def _target_payload(target: ModelOperationTarget) -> dict[str, object]:
    return {
        "provider_kind": target.provider_kind,
        "endpoint": _endpoint_payload(target.provider_endpoint),
        "requested_target": target.requested_target,
        "resolved_model_ref": target.model_ref,
        "resolved_model_candidate": target.model_candidate_name,
    }


def _progress_summary(progress: Sequence[PullProgress]) -> dict[str, object]:
    if not progress:
        return {
            "event_count": 0,
            "last_status": None,
            "completed_bytes": None,
            "total_bytes": None,
        }
    last = progress[-1]
    return {
        "event_count": len(progress),
        "last_status": last.status,
        "completed_bytes": last.completed,
        "total_bytes": last.total,
    }


def run_model_pull(
    config_dir: Path,
    *,
    provider_kind: str | None,
    model_candidate_name: str | None,
    model_ref: str | None,
    adapter_factory: Callable[[ProviderEndpoint], object] | None = None,
    on_progress: Callable[[PullProgress], None] | None = None,
) -> dict[str, object]:
    """model pull の JSON 正準形を返す."""
    if adapter_factory is None:
        adapter_factory = build_adapter
    target = resolve_model_operation_target(
        config_dir,
        provider_kind=provider_kind,
        model_candidate_name=model_candidate_name,
        model_ref=model_ref,
    )
    try:
        adapter = adapter_factory(target.provider_endpoint)
    except Exception as exc:
        raise ConfigurationError(
            f"provider adapter 構築失敗 ({target.provider_kind}): {exc}"
        ) from exc
    result = adapter.pull(target.model_ref, on_progress=on_progress)
    blocking_issue_count = 0 if result.state != "failed" else 1
    return {
        "target": _target_payload(target),
        "pull": {
            "state": result.state,
            "provider_evidence": result.detail,
            "progress_summary": _progress_summary(result.progress),
        },
        "summary": {
            "blocking_issue_count": blocking_issue_count,
            "next_action": (
                "model_warmup"
                if blocking_issue_count == 0
                else "fix_pull_and_retry"
            ),
        },
    }


def render_model_pull_markdown(payload: Mapping[str, object]) -> str:
    """model pull の Markdown 表示を生成する."""
    target = payload.get("target") or {}
    pull = payload.get("pull") or {}
    summary = payload.get("summary") or {}
    endpoint = target.get("endpoint") or {}
    progress = pull.get("progress_summary") or {}

    lines = ["# model pull", "", "## target"]
    lines.append(
        "- Provider: "
        f"{target.get('provider_kind', 'unknown')}@"
        f"{endpoint.get('host', '-')}:"
        f"{endpoint.get('port', '-')}"
    )
    lines.append(
        f"- Requested target: {target.get('requested_target', 'unknown')}"
    )
    lines.append(
        f"- Resolved model ref: {target.get('resolved_model_ref', 'unknown')}"
    )
    lines.append(
        "- Resolved model candidate: "
        f"{target.get('resolved_model_candidate', 'none')}"
    )

    lines.extend(["", "## pull"])
    lines.append(f"- State: {pull.get('state', 'unknown')}")
    lines.append(f"- Evidence: {pull.get('provider_evidence', '')}")
    lines.append(
        "- Progress summary: "
        f"events={progress.get('event_count', 0)}, "
        f"last_status={progress.get('last_status', 'none')}, "
        f"completed_bytes={progress.get('completed_bytes', 'unknown')}, "
        f"total_bytes={progress.get('total_bytes', 'unknown')}"
    )

    lines.extend(["", "## summary"])
    lines.append(
        f"- Blocking issue count: {summary.get('blocking_issue_count', 0)}"
    )
    lines.append(f"- Next action: {summary.get('next_action', 'unknown')}")
    return "\n".join(lines) + "\n"


def run_model_warmup(
    config_dir: Path,
    *,
    provider_kind: str | None,
    model_candidate_name: str | None,
    model_ref: str | None,
    adapter_factory: Callable[[ProviderEndpoint], object] | None = None,
) -> dict[str, object]:
    """model warmup の JSON 正準形を返す."""
    if adapter_factory is None:
        adapter_factory = build_adapter
    target = resolve_model_operation_target(
        config_dir,
        provider_kind=provider_kind,
        model_candidate_name=model_candidate_name,
        model_ref=model_ref,
    )
    try:
        adapter = adapter_factory(target.provider_endpoint)
    except Exception as exc:
        raise ConfigurationError(
            f"provider adapter 構築失敗 ({target.provider_kind}): {exc}"
        ) from exc
    result = adapter.warmup(target.model_ref)
    blocking_issue_count = 0 if result.state == "ready" else 1
    return {
        "target": _target_payload(target),
        "warmup": {
            "state": result.state,
            "elapsed_seconds": result.elapsed_seconds,
            "provider_evidence": result.detail,
            "provider_metadata": dict(result.metadata),
        },
        "summary": {
            "blocking_issue_count": blocking_issue_count,
            "next_action": (
                "system_probe_or_run"
                if blocking_issue_count == 0
                else "fix_warmup_and_retry"
            ),
        },
    }


def render_model_warmup_markdown(payload: Mapping[str, object]) -> str:
    """model warmup の Markdown 表示を生成する."""
    target = payload.get("target") or {}
    warmup = payload.get("warmup") or {}
    summary = payload.get("summary") or {}
    endpoint = target.get("endpoint") or {}

    lines = ["# model warmup", "", "## target"]
    lines.append(
        "- Provider: "
        f"{target.get('provider_kind', 'unknown')}@"
        f"{endpoint.get('host', '-')}:"
        f"{endpoint.get('port', '-')}"
    )
    lines.append(
        f"- Requested target: {target.get('requested_target', 'unknown')}"
    )
    lines.append(
        f"- Resolved model ref: {target.get('resolved_model_ref', 'unknown')}"
    )
    lines.append(
        "- Resolved model candidate: "
        f"{target.get('resolved_model_candidate', 'none')}"
    )

    lines.extend(["", "## warmup"])
    lines.append(f"- State: {warmup.get('state', 'unknown')}")
    lines.append(
        f"- Elapsed seconds: {warmup.get('elapsed_seconds', 'unknown')}"
    )
    lines.append(f"- Evidence: {warmup.get('provider_evidence', '')}")
    lines.append(
        f"- Provider metadata: {warmup.get('provider_metadata', {})}"
    )

    lines.extend(["", "## summary"])
    lines.append(
        f"- Blocking issue count: {summary.get('blocking_issue_count', 0)}"
    )
    lines.append(f"- Next action: {summary.get('next_action', 'unknown')}")
    return "\n".join(lines) + "\n"
