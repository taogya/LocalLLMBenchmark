"""Ollama Provider Adapter (TASK-00007-01, COMP-00005, PVD-00401).

v1 唯一の実装。Ollama の `/api/generate` (非ストリーミング) を呼ぶ。
Python 標準の `urllib` のみで HTTP を実行する (NFR-00302)。

Ollama 固有のレスポンス形状を契約面に持ち込まない (PVD-00001) ため、
このモジュールは生応答を `raw_response` にそのまま乗せ、上位層には
標準化済み `InferenceResponse` のみを返す。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from ..models import InferenceRequest, InferenceResponse, ProviderEndpoint
from .base import (
    FAILURE_MALFORMED_RESPONSE,
    FAILURE_MODEL_NOT_FOUND,
    FAILURE_PROVIDER_RUNTIME,
    FAILURE_PROVIDER_UNREACHABLE,
    FAILURE_TIMEOUT,
    FAILURE_UNSUPPORTED_REQUEST,
)


@dataclass(frozen=True)
class OllamaAdapter:
    """Ollama 用 Provider Adapter."""

    endpoint: ProviderEndpoint

    def _provider_identity(self, model_ref: str) -> dict[str, object]:
        # PVD-00208: provider 種別 + 接続先概要 + モデル参照
        return {
            "kind": self.endpoint.kind,
            "host": self.endpoint.host,
            "port": self.endpoint.port,
            "model_ref": model_ref,
        }

    def _build_payload(self, request: InferenceRequest) -> dict[str, object]:
        options: dict[str, object] = {}
        if request.generation.temperature is not None:
            options["temperature"] = request.generation.temperature
        if request.generation.seed is not None:
            options["seed"] = request.generation.seed
        if request.generation.max_tokens is not None:
            # Ollama は num_predict をトークン上限として扱う
            options["num_predict"] = request.generation.max_tokens
        payload: dict[str, object] = {
            "model": request.model_ref,
            "prompt": request.prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options
        return payload

    def _validate_generation(
        self, request: InferenceRequest
    ) -> str | None:
        """生成条件の事前妥当性検査 (PVD-00306).

        Ollama が解釈不能な値 (負の温度・0 以下の num_predict 等) を
        手元で弾く。問題があれば短い理由文を返し、なければ None。
        """
        gen = request.generation
        if gen.temperature is not None and gen.temperature < 0:
            return f"temperature は 0 以上を指定する (指定: {gen.temperature})"
        if gen.max_tokens is not None and gen.max_tokens <= 0:
            return f"max_tokens は 1 以上を指定する (指定: {gen.max_tokens})"
        if gen.seed is not None and not isinstance(gen.seed, int):
            return f"seed は整数で指定する (指定: {gen.seed!r})"
        if not request.prompt:
            return "prompt が空"
        if not request.model_ref:
            return "model_ref が空"
        return None


    def infer(self, request: InferenceRequest) -> InferenceResponse:
        url = f"http://{self.endpoint.host}:{self.endpoint.port}/api/generate"
        identity = self._provider_identity(request.model_ref)

        # PVD-00306 unsupported_request: provider に届ける前の事前検査.
        # Ollama が解釈できる範囲を逸脱した生成条件 (負の温度・0 以下の
        # max_tokens 等) は実行時検出 (HTTP 400) より早く落とす.
        unsupported = self._validate_generation(request)
        if unsupported is not None:
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=0.0,
                input_tokens=None,
                output_tokens=None,
                raw_response={"validation_error": unsupported},
                provider_identity=identity,
                failure_kind=FAILURE_UNSUPPORTED_REQUEST,
                failure_detail=unsupported,
            )

        payload = self._build_payload(request)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        timeout = (
            request.timeout_seconds
            if request.timeout_seconds is not None
            else self.endpoint.timeout_seconds
        )
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
        except urllib.error.HTTPError as exc:
            elapsed = time.perf_counter() - started
            # Ollama は不明モデルで 404、不正リクエストで 400 を返す.
            if exc.code == 404:
                kind = FAILURE_MODEL_NOT_FOUND
            elif exc.code == 400:
                # PVD-00306: 生成条件等を provider が解釈できない
                kind = FAILURE_UNSUPPORTED_REQUEST
            else:
                kind = FAILURE_PROVIDER_RUNTIME
            try:
                detail_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail_body = ""
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=elapsed,
                input_tokens=None,
                output_tokens=None,
                raw_response={"http_status": exc.code, "body": detail_body},
                provider_identity=identity,
                failure_kind=kind,
                failure_detail=f"HTTP {exc.code}: {detail_body[:200]}",
            )
        except urllib.error.URLError as exc:
            elapsed = time.perf_counter() - started
            reason = getattr(exc, "reason", exc)
            # タイムアウトは socket.timeout として URLError.reason に入る
            kind = (
                FAILURE_TIMEOUT
                if isinstance(reason, TimeoutError)
                or "timed out" in str(reason).lower()
                else FAILURE_PROVIDER_UNREACHABLE
            )
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=elapsed,
                input_tokens=None,
                output_tokens=None,
                raw_response={"error": str(reason)},
                provider_identity=identity,
                failure_kind=kind,
                failure_detail=str(reason),
            )
        except TimeoutError as exc:
            elapsed = time.perf_counter() - started
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=elapsed,
                input_tokens=None,
                output_tokens=None,
                raw_response={"error": str(exc)},
                provider_identity=identity,
                failure_kind=FAILURE_TIMEOUT,
                failure_detail=str(exc),
            )

        elapsed = time.perf_counter() - started
        try:
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=elapsed,
                input_tokens=None,
                output_tokens=None,
                raw_response={"bytes_len": len(raw_bytes)},
                provider_identity=identity,
                failure_kind=FAILURE_MALFORMED_RESPONSE,
                failure_detail=f"JSON 解析失敗: {exc}",
            )
        if not isinstance(raw, dict) or "response" not in raw:
            return InferenceResponse(
                response_text=None,
                elapsed_seconds=elapsed,
                input_tokens=None,
                output_tokens=None,
                raw_response=raw,
                provider_identity=identity,
                failure_kind=FAILURE_MALFORMED_RESPONSE,
                failure_detail="Ollama 応答に 'response' キーが無い",
            )
        response_text = str(raw.get("response", ""))
        # PVD-00203 / PVD-00204: provider が返さない場合は欠損扱い
        input_tokens = raw.get("prompt_eval_count")
        output_tokens = raw.get("eval_count")
        return InferenceResponse(
            response_text=response_text,
            elapsed_seconds=elapsed,
            input_tokens=int(input_tokens) if isinstance(input_tokens, int) else None,
            output_tokens=int(output_tokens) if isinstance(output_tokens, int) else None,
            raw_response=raw,
            provider_identity=identity,
        )


def build_adapter(endpoint: ProviderEndpoint) -> OllamaAdapter:
    """provider 種別から Adapter を構築する.

    Phase 1 では `ollama` のみ対応。
    """
    if endpoint.kind != "ollama":
        raise ValueError(
            f"Phase 1 では provider 種別 'ollama' のみ対応 (指定: {endpoint.kind})"
        )
    return OllamaAdapter(endpoint=endpoint)
