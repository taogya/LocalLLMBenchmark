"""task_id 00001-03: provider 実装の共通抽象。"""

from __future__ import annotations

from typing import Protocol

from local_llm_benchmark.benchmark.models import (
    InferenceRequest,
    InferenceResponse,
)


class ProviderError(RuntimeError):
    pass


class ProviderConnectionError(ProviderError):
    pass


class ProviderResponseError(ProviderError):
    pass


class ProviderAdapter(Protocol):
    provider_id: str

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        ...
