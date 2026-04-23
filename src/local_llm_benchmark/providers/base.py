"""Provider Adapter 共通契約 (
TASK-00007-01 / TASK-00012-02 / TASK-00013-02 / TASK-00014-02,
COMP-00005, PVD-).

設計原則:
- PVD-00001 上位層は標準化された InferenceRequest / Response のみを扱う
- PVD-00405 1 Run = 1 Model: Adapter は単一モデル参照を前提とする
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, Sequence

from ..models import InferenceRequest, InferenceResponse


# 失敗種別 (PVD-00301..00307)
FAILURE_PROVIDER_UNREACHABLE = "provider_unreachable"
FAILURE_MODEL_NOT_FOUND = "model_not_found"
FAILURE_TIMEOUT = "timeout"
FAILURE_MALFORMED_RESPONSE = "malformed_response"
FAILURE_PROVIDER_RUNTIME = "provider_runtime_error"
FAILURE_UNSUPPORTED_REQUEST = "unsupported_request"

# probe 状態 (PVD-00209 / PVD-00210)
PROBE_REACHABLE = "reachable"
PROBE_UNREACHABLE = "unreachable"
PROBE_UNKNOWN = "unknown"
MODEL_AVAILABLE = "available"
MODEL_MISSING = "missing"
MODEL_UNKNOWN = "unknown"

# Run 中断候補とみなす失敗種別 (PVD-00301/00302/00306)
RUN_ABORT_FAILURE_KINDS: frozenset[str] = frozenset(
    {
        FAILURE_PROVIDER_UNREACHABLE,
        FAILURE_MODEL_NOT_FOUND,
        FAILURE_UNSUPPORTED_REQUEST,
    }
)


@dataclass(frozen=True)
class ProviderProbeResult:
    """provider 到達確認の標準化結果 (PVD-00106 / PVD-00209 / PVD-00211)."""

    status: str
    detail: str
    raw_response: Any
    provider_identity: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelProbeResult:
    """model ref 解決の標準化結果 (PVD-00107 / PVD-00210 / PVD-00211)."""

    model_ref: str
    status: str
    detail: str
    raw_response: Any
    provider_identity: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatusResult:
    """provider status snapshot の標準化結果 (PVD-00108 / PVD-00212 / PVD-00213)."""

    status: str
    detail: str
    raw_response: Any
    provider_identity: Mapping[str, Any]
    version_info: Mapping[str, Any] = field(default_factory=dict)
    inventory: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PullProgress:
    """pull 進捗 1 件 (PVD-00214)."""

    status: str
    digest: str | None
    total: int | None
    completed: int | None
    raw_response: Any


@dataclass(frozen=True)
class PullResult:
    """model pull の標準化結果 (PVD-00109 / PVD-00214)."""

    state: str
    detail: str
    raw_response: Any
    provider_identity: Mapping[str, Any]
    progress: Sequence[PullProgress] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WarmupResult:
    """model warmup の標準化結果 (PVD-00110 / PVD-00215)."""

    state: str
    detail: str
    elapsed_seconds: float
    raw_response: Any
    provider_identity: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    """Provider Adapter の構造的契約 (COMP-00005).

    Run Coordinator はこの Protocol だけを参照する。
    """

    def infer(
        self, request: InferenceRequest
    ) -> InferenceResponse:  # pragma: no cover
        ...

    def validate_request(
        self, request: InferenceRequest
    ) -> str | None:  # pragma: no cover
        ...

    def probe(
        self, model_refs: Sequence[str]
    ) -> tuple[
        ProviderProbeResult,
        Mapping[str, ModelProbeResult],
    ]:  # pragma: no cover
        ...

    def status(self) -> ProviderStatusResult:  # pragma: no cover
        ...

    def pull(
        self,
        model_ref: str,
        on_progress: Callable[[PullProgress], None] | None = None,
    ) -> PullResult:  # pragma: no cover
        ...

    def warmup(self, model_ref: str) -> WarmupResult:  # pragma: no cover
        ...
