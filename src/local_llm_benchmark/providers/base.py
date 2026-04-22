"""Provider Adapter 共通契約 (TASK-00007-01, COMP-00005, PVD-).

設計原則:
- PVD-00001 上位層は標準化された InferenceRequest / Response のみを扱う
- PVD-00405 1 Run = 1 Model: Adapter は単一モデル参照を前提とする
"""

from __future__ import annotations

from typing import Protocol

from ..models import InferenceRequest, InferenceResponse


# 失敗種別 (PVD-00301..00307)
FAILURE_PROVIDER_UNREACHABLE = "provider_unreachable"
FAILURE_MODEL_NOT_FOUND = "model_not_found"
FAILURE_TIMEOUT = "timeout"
FAILURE_MALFORMED_RESPONSE = "malformed_response"
FAILURE_PROVIDER_RUNTIME = "provider_runtime_error"
FAILURE_UNSUPPORTED_REQUEST = "unsupported_request"

# Run 中断候補とみなす失敗種別 (PVD-00301/00302/00306)
RUN_ABORT_FAILURE_KINDS: frozenset[str] = frozenset(
    {
        FAILURE_PROVIDER_UNREACHABLE,
        FAILURE_MODEL_NOT_FOUND,
        FAILURE_UNSUPPORTED_REQUEST,
    }
)


class ProviderAdapter(Protocol):
    """Provider Adapter の構造的契約 (COMP-00005).

    Run Coordinator はこの Protocol だけを参照する。
    """

    def infer(self, request: InferenceRequest) -> InferenceResponse:  # pragma: no cover
        ...
