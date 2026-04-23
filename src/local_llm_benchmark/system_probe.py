"""system-probe の収集・整形 (TASK-00012-02, COMP-00001 / COMP-00005 / COMP-00007).

`check` の静的検証とは分離し、host facts と provider/model の外部状態だけを
観測する。
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .config import ConfigurationError, load_model_candidates, load_provider_endpoints
from .models import ModelCandidate, ProviderEndpoint
from .providers import (
    MODEL_UNKNOWN,
    PROBE_REACHABLE,
    PROBE_UNKNOWN,
    build_adapter,
)


def _run_command(command: Sequence[str], *, timeout: float = 5.0) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        return False, detail or f"exit={completed.returncode}"
    return True, completed.stdout.strip()


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _parse_size_text(text: str | None) -> int | None:
    if text is None:
        return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]i?B|[KMGTP]B)", text, re.I)
    if m is None:
        return None
    value = float(m.group(1))
    unit = m.group(2).upper()
    power = {
        "KB": 1,
        "KIB": 1,
        "MB": 2,
        "MIB": 2,
        "GB": 3,
        "GIB": 3,
        "TB": 4,
        "TIB": 4,
        "PB": 5,
        "PIB": 5,
    }.get(unit)
    if power is None:
        return None
    return int(value * (1024 ** power))


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    current = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if current < 1024.0 or unit == "TiB":
            if unit == "B":
                return f"{int(current)} {unit}"
            return f"{current:.1f} {unit}"
        current /= 1024.0
    return f"{value} B"


def _mac_sysctl(name: str) -> str | None:
    ok, output = _run_command(["sysctl", "-n", name])
    return output if ok else None


def _linux_cpu_name() -> str | None:
    text = _read_text(Path("/proc/cpuinfo"))
    if text is None:
        return None
    for line in text.splitlines():
        if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def _linux_physical_cores() -> int | None:
    text = _read_text(Path("/proc/cpuinfo"))
    if text is None:
        return None
    pairs: set[tuple[str, str]] = set()
    fallback: int | None = None
    current_physical: str | None = None
    for line in text.splitlines():
        if not line.strip():
            current_physical = None
            continue
        if line.lower().startswith("physical id"):
            current_physical = line.split(":", 1)[1].strip()
        elif line.lower().startswith("core id") and current_physical is not None:
            core_id = line.split(":", 1)[1].strip()
            pairs.add((current_physical, core_id))
        elif line.lower().startswith("cpu cores") and fallback is None:
            try:
                fallback = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
    if pairs:
        return len(pairs)
    return fallback


def _linux_total_memory() -> int | None:
    text = _read_text(Path("/proc/meminfo"))
    if text is None:
        return None
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1]) * 1024
                except ValueError:
                    return None
    return None


def _collect_linux_gpus() -> tuple[list[dict[str, object]], str]:
    ok, output = _run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total",
            "--format=csv,noheader,nounits",
        ]
    )
    if ok:
        gpus: list[dict[str, object]] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = [part.strip() for part in line.split(",", 1)]
            name = parts[0]
            vram_bytes = None
            if len(parts) == 2:
                try:
                    vram_bytes = int(parts[1]) * 1024 * 1024
                except ValueError:
                    vram_bytes = None
            gpus.append({"name": name, "vram_bytes": vram_bytes})
        if gpus:
            return gpus, "nvidia-smi"

    ok, output = _run_command(["lspci"])
    if ok:
        lines = []
        for line in output.splitlines():
            lowered = line.lower()
            if (
                "vga compatible controller" in lowered
                or "3d controller" in lowered
                or "display controller" in lowered
            ):
                lines.append(line)
        gpus = [{"name": line.split(": ", 1)[-1], "vram_bytes": None} for line in lines]
        if gpus:
            return gpus, "lspci"
        return [], "lspci では GPU を検出できなかった"

    return [], "GPU 情報を取得できる標準コマンドが見つからない"


def _collect_macos_gpus() -> tuple[list[dict[str, object]], str]:
    ok, output = _run_command(["system_profiler", "SPDisplaysDataType", "-json"], timeout=10.0)
    if not ok:
        return [], output or "system_profiler 実行失敗"
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        return [], f"system_profiler JSON 解析失敗: {exc}"
    items = payload.get("SPDisplaysDataType") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return [], "system_profiler 応答に SPDisplaysDataType が無い"
    gpus: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("sppci_model") or item.get("_name") or "unknown"
        vram = (
            item.get("spdisplays_vram")
            or item.get("spdisplays_vram_shared")
            or item.get("spdisplays_vram_dyn")
        )
        gpus.append(
            {
                "name": str(name),
                "vram_bytes": _parse_size_text(str(vram)) if vram is not None else None,
            }
        )
    if not gpus:
        return [], "system_profiler では GPU を検出できなかった"
    return gpus, "system_profiler"


def collect_system_snapshot() -> dict[str, object]:
    """host facts を best-effort で収集する."""
    system_name = platform.system()
    if system_name == "Darwin":
        os_name = "macOS"
        os_version = platform.mac_ver()[0] or platform.release()
        cpu_name = _mac_sysctl("machdep.cpu.brand_string") or platform.processor() or "unknown"
        physical_cores = _mac_sysctl("hw.physicalcpu")
        logical_cores = _mac_sysctl("hw.logicalcpu")
        total_memory = _mac_sysctl("hw.memsize")
        gpus, gpu_detail = _collect_macos_gpus()
    elif system_name == "Linux":
        os_name = "Linux"
        os_version = platform.release()
        cpu_name = _linux_cpu_name() or platform.processor() or "unknown"
        physical_cores = _linux_physical_cores()
        logical_cores = os.cpu_count()
        total_memory = _linux_total_memory()
        gpus, gpu_detail = _collect_linux_gpus()
    else:
        os_name = system_name or "unknown"
        os_version = platform.release()
        cpu_name = platform.processor() or "unknown"
        physical_cores = None
        logical_cores = os.cpu_count()
        total_memory = None
        gpus = []
        gpu_detail = f"未対応 OS: {system_name or 'unknown'}"

    if isinstance(physical_cores, str):
        try:
            physical_cores = int(physical_cores)
        except ValueError:
            physical_cores = None
    if isinstance(logical_cores, str):
        try:
            logical_cores = int(logical_cores)
        except ValueError:
            logical_cores = None
    if isinstance(total_memory, str):
        try:
            total_memory = int(total_memory)
        except ValueError:
            total_memory = None

    return {
        "os": {
            "name": os_name,
            "version": os_version,
            "machine": platform.machine() or "unknown",
        },
        "cpu": {
            "name": cpu_name,
            "physical_cores": physical_cores,
            "logical_cores": logical_cores,
        },
        "memory": {
            "total_bytes": total_memory,
            "total_human": _format_bytes(total_memory),
        },
        "gpus": gpus,
        "gpu_probe": {
            "status": "detected" if gpus else "unknown",
            "detail": gpu_detail,
        },
    }


def _provider_identity(endpoint: ProviderEndpoint, model_ref: str | None = None) -> dict[str, object]:
    return {
        "kind": endpoint.kind,
        "host": endpoint.host,
        "port": endpoint.port,
        "model_ref": model_ref,
    }


def _host_facts_summary(system_snapshot: Mapping[str, object]) -> dict[str, object]:
    os_info = system_snapshot.get("os") or {}
    cpu = system_snapshot.get("cpu") or {}
    memory = system_snapshot.get("memory") or {}
    gpus = system_snapshot.get("gpus") or []
    return {
        "os": f"{os_info.get('name', 'unknown')} {os_info.get('version', 'unknown')}",
        "cpu": cpu.get("name") or "unknown",
        "physical_cores": cpu.get("physical_cores") if cpu.get("physical_cores") is not None else "unknown",
        "logical_cores": cpu.get("logical_cores") if cpu.get("logical_cores") is not None else "unknown",
        "total_memory_bytes": memory.get("total_bytes"),
        "total_memory_human": memory.get("total_human") or "unknown",
        "gpu_names": [gpu.get("name") for gpu in gpus if isinstance(gpu, dict) and gpu.get("name")],
        "gpu_vram_bytes": [gpu.get("vram_bytes") for gpu in gpus if isinstance(gpu, dict)],
    }


def _count_statuses(items: Sequence[Mapping[str, object]]) -> dict[str, int]:
    counter = Counter(str(item.get("status")) for item in items)
    return dict(sorted(counter.items()))


def run_system_probe(
    config_dir: Path,
    *,
    adapter_factory: Callable[[ProviderEndpoint], object] | None = None,
) -> dict[str, object]:
    """Provider / ModelCandidate 定義を読み、system-probe の JSON 正準形を返す."""
    if adapter_factory is None:
        adapter_factory = build_adapter
    models = load_model_candidates(config_dir / "model_candidates.toml")
    providers = load_provider_endpoints(config_dir / "providers.toml")
    system_snapshot = collect_system_snapshot()

    provider_rows: list[dict[str, object]] = []
    model_rows: list[dict[str, object]] = []
    grouped: dict[str, list[ModelCandidate]] = defaultdict(list)
    for candidate in models.values():
        grouped[candidate.provider_kind].append(candidate)

    provider_kinds = sorted(set(providers.keys()) | set(grouped.keys()))
    for provider_kind in provider_kinds:
        endpoint = providers.get(provider_kind)
        candidates = sorted(grouped.get(provider_kind, []), key=lambda item: item.name)
        if endpoint is None:
            provider_rows.append(
                {
                    "provider_kind": provider_kind,
                    "endpoint": None,
                    "status": PROBE_UNKNOWN,
                    "evidence": "providers.toml に接続先定義が無いため probe できない",
                    "provider_identity": {
                        "kind": provider_kind,
                        "host": None,
                        "port": None,
                        "model_ref": None,
                    },
                    "metadata": {},
                }
            )
            for candidate in candidates:
                model_rows.append(
                    {
                        "name": candidate.name,
                        "label": candidate.label,
                        "provider_kind": candidate.provider_kind,
                        "provider_model_ref": candidate.provider_model_ref,
                        "status": MODEL_UNKNOWN,
                        "evidence": "provider 接続先が未定義",
                    }
                )
            continue

        try:
            adapter = adapter_factory(endpoint)
        except Exception as exc:
            provider_rows.append(
                {
                    "provider_kind": provider_kind,
                    "endpoint": {
                        "host": endpoint.host,
                        "port": endpoint.port,
                        "timeout_seconds": endpoint.timeout_seconds,
                    },
                    "status": PROBE_UNKNOWN,
                    "evidence": f"adapter 初期化失敗: {exc}",
                    "provider_identity": _provider_identity(endpoint),
                    "metadata": {},
                }
            )
            for candidate in candidates:
                model_rows.append(
                    {
                        "name": candidate.name,
                        "label": candidate.label,
                        "provider_kind": candidate.provider_kind,
                        "provider_model_ref": candidate.provider_model_ref,
                        "status": MODEL_UNKNOWN,
                        "evidence": f"adapter 初期化失敗: {exc}",
                    }
                )
            continue

        try:
            provider_probe, model_probes = adapter.probe(
                [candidate.provider_model_ref for candidate in candidates]
            )
        except Exception as exc:
            provider_rows.append(
                {
                    "provider_kind": provider_kind,
                    "endpoint": {
                        "host": endpoint.host,
                        "port": endpoint.port,
                        "timeout_seconds": endpoint.timeout_seconds,
                    },
                    "status": PROBE_UNKNOWN,
                    "evidence": f"provider probe 失敗: {exc}",
                    "provider_identity": _provider_identity(endpoint),
                    "metadata": {},
                }
            )
            for candidate in candidates:
                model_rows.append(
                    {
                        "name": candidate.name,
                        "label": candidate.label,
                        "provider_kind": candidate.provider_kind,
                        "provider_model_ref": candidate.provider_model_ref,
                        "status": MODEL_UNKNOWN,
                        "evidence": f"provider probe 失敗: {exc}",
                    }
                )
            continue

        provider_rows.append(
            {
                "provider_kind": provider_kind,
                "endpoint": {
                    "host": endpoint.host,
                    "port": endpoint.port,
                    "timeout_seconds": endpoint.timeout_seconds,
                },
                "status": provider_probe.status,
                "evidence": provider_probe.detail,
                "provider_identity": dict(provider_probe.provider_identity),
                "metadata": dict(provider_probe.metadata),
            }
        )
        for candidate in candidates:
            model_probe = model_probes.get(candidate.provider_model_ref)
            if model_probe is None:
                status = MODEL_UNKNOWN
                evidence = "adapter が model ref の判定結果を返さなかった"
            else:
                status = model_probe.status
                evidence = model_probe.detail
            model_rows.append(
                {
                    "name": candidate.name,
                    "label": candidate.label,
                    "provider_kind": candidate.provider_kind,
                    "provider_model_ref": candidate.provider_model_ref,
                    "status": status,
                    "evidence": evidence,
                }
            )

    model_rows.sort(key=lambda item: str(item["name"]))
    provider_status_counts = _count_statuses(provider_rows)
    model_status_counts = _count_statuses(model_rows)
    probe_negative = any(
        item.get("status") != PROBE_REACHABLE for item in provider_rows
    ) or any(item.get("status") != "available" for item in model_rows)

    return {
        "system": system_snapshot,
        "providers": provider_rows,
        "model_candidates": model_rows,
        "summary": {
            "provider_problem_count": sum(
                1 for item in provider_rows if item.get("status") != PROBE_REACHABLE
            ),
            "provider_status_counts": provider_status_counts,
            "model_status_counts": model_status_counts,
            "host_facts": _host_facts_summary(system_snapshot),
            "probe_negative": probe_negative,
        },
    }


def render_system_probe_markdown(payload: Mapping[str, object]) -> str:
    """system-probe の人間可読表示を生成する."""
    system = payload.get("system") or {}
    providers = payload.get("providers") or []
    models = payload.get("model_candidates") or []
    summary = payload.get("summary") or {}
    os_info = system.get("os") or {}
    cpu = system.get("cpu") or {}
    memory = system.get("memory") or {}
    gpu_probe = system.get("gpu_probe") or {}
    gpus = system.get("gpus") or []

    lines = ["# system-probe", "", "## system"]
    lines.append(f"- OS: {os_info.get('name', 'unknown')} {os_info.get('version', 'unknown')}")
    lines.append(f"- CPU: {cpu.get('name') or 'unknown'}")
    lines.append(
        f"- Physical cores: {cpu.get('physical_cores') if cpu.get('physical_cores') is not None else 'unknown'}"
    )
    lines.append(
        f"- Logical cores: {cpu.get('logical_cores') if cpu.get('logical_cores') is not None else 'unknown'}"
    )
    lines.append(f"- Total memory: {memory.get('total_human') or 'unknown'}")
    lines.append(
        f"- GPU probe: {gpu_probe.get('status', 'unknown')} ({gpu_probe.get('detail', 'unknown')})"
    )
    if gpus:
        lines.append("")
        lines.append("| GPU | VRAM |")
        lines.append("| --- | --- |")
        for gpu in gpus:
            if not isinstance(gpu, dict):
                continue
            lines.append(
                f"| {gpu.get('name', 'unknown')} | {_format_bytes(gpu.get('vram_bytes')) if isinstance(gpu.get('vram_bytes'), int) else 'unknown'} |"
            )
    else:
        lines.append("- GPU: unknown")

    lines.extend(["", "## providers"])
    if providers:
        lines.append("| Provider | Endpoint | Status | Evidence |")
        lines.append("| --- | --- | --- | --- |")
        for provider in providers:
            if not isinstance(provider, dict):
                continue
            endpoint = provider.get("endpoint") or {}
            endpoint_text = (
                f"{endpoint.get('host', '-') }:{endpoint.get('port', '-') }"
                if isinstance(endpoint, dict) and endpoint
                else "-"
            )
            lines.append(
                f"| {provider.get('provider_kind', 'unknown')} | {endpoint_text} | {provider.get('status', 'unknown')} | {provider.get('evidence', '')} |"
            )
    else:
        lines.append("- provider 定義なし")

    lines.extend(["", "## model_candidates"])
    if models:
        lines.append("| Name | Provider | Model Ref | Status | Evidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for model in models:
            if not isinstance(model, dict):
                continue
            lines.append(
                f"| {model.get('name', 'unknown')} | {model.get('provider_kind', 'unknown')} | {model.get('provider_model_ref', 'unknown')} | {model.get('status', 'unknown')} | {model.get('evidence', '')} |"
            )
    else:
        lines.append("- model candidate 定義なし")

    lines.extend(["", "## summary"])
    lines.append(f"- Provider problems: {summary.get('provider_problem_count', 0)}")
    lines.append(f"- Provider status counts: {summary.get('provider_status_counts', {})}")
    lines.append(f"- Model status counts: {summary.get('model_status_counts', {})}")
    lines.append(f"- Host facts: {summary.get('host_facts', {})}")
    lines.append(
        f"- Probe negative: {'yes' if summary.get('probe_negative') else 'no'}"
    )
    return "\n".join(lines) + "\n"


def emit_probe_issues(payload: Mapping[str, object]) -> list[str]:
    """probe-negative 判定につながる項目を 1 行 1 件で返す."""
    issues: list[str] = []
    for provider in payload.get("providers") or []:
        if not isinstance(provider, dict) or provider.get("status") == PROBE_REACHABLE:
            continue
        endpoint = provider.get("endpoint") or {}
        endpoint_text = (
            f"{endpoint.get('host', '-') }:{endpoint.get('port', '-') }"
            if isinstance(endpoint, dict) and endpoint
            else "-"
        )
        issues.append(
            "[system-probe] provider "
            f"{provider.get('provider_kind', 'unknown')}@{endpoint_text}: "
            f"{provider.get('status', PROBE_UNKNOWN)} - {provider.get('evidence', '')}"
        )
    for model in payload.get("model_candidates") or []:
        if not isinstance(model, dict) or model.get("status") == "available":
            continue
        issues.append(
            "[system-probe] model "
            f"{model.get('name', 'unknown')} ({model.get('provider_model_ref', 'unknown')}): "
            f"{model.get('status', MODEL_UNKNOWN)} - {model.get('evidence', '')}"
        )
    return issues