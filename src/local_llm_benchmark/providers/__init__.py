"""Provider Adapter 公開窓口 (TASK-00007-01)."""

from .base import (
    FAILURE_MALFORMED_RESPONSE,
    FAILURE_MODEL_NOT_FOUND,
    FAILURE_PROVIDER_RUNTIME,
    FAILURE_PROVIDER_UNREACHABLE,
    FAILURE_TIMEOUT,
    FAILURE_UNSUPPORTED_REQUEST,
    RUN_ABORT_FAILURE_KINDS,
    ProviderAdapter,
)
from .ollama import OllamaAdapter, build_adapter

__all__ = [
    "FAILURE_MALFORMED_RESPONSE",
    "FAILURE_MODEL_NOT_FOUND",
    "FAILURE_PROVIDER_RUNTIME",
    "FAILURE_PROVIDER_UNREACHABLE",
    "FAILURE_TIMEOUT",
    "FAILURE_UNSUPPORTED_REQUEST",
    "OllamaAdapter",
    "ProviderAdapter",
    "RUN_ABORT_FAILURE_KINDS",
    "build_adapter",
]
