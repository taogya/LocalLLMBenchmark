"""Ollama Provider Adapter (
TASK-00007-01 / TASK-00012-02 / TASK-00013-02 / TASK-00014-02,
COMP-00005, PVD-00401).

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
from typing import Callable, Mapping, Sequence

from ..models import InferenceRequest, InferenceResponse, ProviderEndpoint
from .base import (
    FAILURE_MALFORMED_RESPONSE,
    FAILURE_MODEL_NOT_FOUND,
    FAILURE_PROVIDER_RUNTIME,
    FAILURE_PROVIDER_UNREACHABLE,
    FAILURE_TIMEOUT,
    FAILURE_UNSUPPORTED_REQUEST,
    MODEL_AVAILABLE,
    MODEL_MISSING,
    MODEL_UNKNOWN,
    PullProgress,
    PullResult,
    PROBE_REACHABLE,
    PROBE_UNREACHABLE,
    PROBE_UNKNOWN,
    ModelProbeResult,
    ProviderProbeResult,
    ProviderStatusResult,
    WarmupResult,
)


@dataclass(frozen=True)
class OllamaAdapter:
    """Ollama 用 Provider Adapter."""

    endpoint: ProviderEndpoint

    def _provider_identity(self, model_ref: str | None) -> dict[str, object]:
        # PVD-00208: provider 種別 + 接続先概要 + モデル参照
        return {
            "kind": self.endpoint.kind,
            "host": self.endpoint.host,
            "port": self.endpoint.port,
            "model_ref": model_ref,
        }

    def _base_url(self) -> str:
        return f"http://{self.endpoint.host}:{self.endpoint.port}"

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, object] | None = None,
        *,
        timeout: float | None = None,
    ) -> object:
        url = f"{self._base_url()}{path}"
        headers = (
            {"Content-Type": "application/json"}
            if payload is not None
            else {}
        )
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers=headers,
        )
        with urllib.request.urlopen(
            req,
            timeout=(
                self.endpoint.timeout_seconds if timeout is None else timeout
            ),
        ) as resp:
            raw_bytes = resp.read()
        try:
            return json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"JSON 解析失敗: {exc}") from exc

    @staticmethod
    def _parse_inventory(raw: object) -> dict[str, Mapping[str, object]]:
        raw_models = raw.get("models") if isinstance(raw, dict) else None
        if not isinstance(raw_models, list):
            raise ValueError("Ollama inventory 応答に 'models' リストが無い")

        inventory: dict[str, Mapping[str, object]] = {}
        for item in raw_models:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if name is None:
                continue
            inventory[str(name)] = item
        return inventory

    def status(self) -> ProviderStatusResult:
        """Ollama の到達状態、版情報、inventory を取得する (TASK-00014-02)."""
        provider_identity = self._provider_identity(None)
        try:
            tags_raw = self._request_json("GET", "/api/tags")
            inventory = self._parse_inventory(tags_raw)
        except urllib.error.HTTPError as exc:
            detail = f"HTTP {exc.code}: inventory 取得失敗"
            return ProviderStatusResult(
                status=PROBE_UNKNOWN,
                detail=detail,
                raw_response={"http_status": exc.code},
                provider_identity=provider_identity,
            )
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            status = (
                PROBE_UNKNOWN
                if isinstance(reason, TimeoutError)
                or "timed out" in str(reason).lower()
                else PROBE_UNREACHABLE
            )
            return ProviderStatusResult(
                status=status,
                detail=str(reason),
                raw_response={"error": str(reason)},
                provider_identity=provider_identity,
            )
        except TimeoutError as exc:
            return ProviderStatusResult(
                status=PROBE_UNKNOWN,
                detail=str(exc),
                raw_response={"error": str(exc)},
                provider_identity=provider_identity,
            )
        except ValueError as exc:
            return ProviderStatusResult(
                status=PROBE_UNKNOWN,
                detail=str(exc),
                raw_response={"error": str(exc)},
                provider_identity=provider_identity,
            )

        version_info: Mapping[str, object] = {"version": "unknown"}
        version_error: str | None = None
        raw_response: dict[str, object] = {"tags": tags_raw}
        try:
            version_raw = self._request_json("GET", "/api/version")
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            ValueError,
        ) as exc:
            version_error = str(getattr(exc, "reason", exc))
            raw_response["version_error"] = version_error
        else:
            if isinstance(version_raw, dict):
                version_info = {
                    str(key): value for key, value in version_raw.items()
                }
            else:
                version_info = {"version": str(version_raw)}
            raw_response["version"] = version_raw

        detail = f"inventory 取得成功: {len(inventory)} model(s)"
        if version_error:
            detail = f"{detail}; version 取得失敗: {version_error}"
        return ProviderStatusResult(
            status=PROBE_REACHABLE,
            detail=detail,
            raw_response=raw_response,
            provider_identity=provider_identity,
            version_info=version_info,
            inventory=tuple(inventory.values()),
            metadata={
                "inventory_count": len(inventory),
                "version_error": version_error,
            },
        )

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

    def validate_request(self, request: InferenceRequest) -> str | None:
        """provider 送信前に request の妥当性を確認する (TASK-00013-02)."""
        return self._validate_generation(request)

    def probe(
        self, model_refs: Sequence[str]
    ) -> tuple[ProviderProbeResult, dict[str, ModelProbeResult]]:
        """Ollama の model inventory から到達確認と model ref 解決を行う."""
        status_snapshot = self.status()
        provider = ProviderProbeResult(
            status=status_snapshot.status,
            detail=status_snapshot.detail,
            raw_response=status_snapshot.raw_response,
            provider_identity=status_snapshot.provider_identity,
            metadata=status_snapshot.metadata,
        )
        if status_snapshot.status != PROBE_REACHABLE:
            return provider, {
                ref: ModelProbeResult(
                    model_ref=ref,
                    status=MODEL_UNKNOWN,
                    detail=(
                        f"provider {status_snapshot.status}:"
                        f" {status_snapshot.detail}"
                    ),
                    raw_response=status_snapshot.raw_response,
                    provider_identity=self._provider_identity(ref),
                )
                for ref in model_refs
            }

        inventory: dict[str, Mapping[str, object]] = {}
        for item in status_snapshot.inventory:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if name is None:
                continue
            inventory[str(name)] = item

        results: dict[str, ModelProbeResult] = {}
        for ref in model_refs:
            matched = inventory.get(ref)
            if matched is None:
                results[ref] = ModelProbeResult(
                    model_ref=ref,
                    status=MODEL_MISSING,
                    detail="provider inventory に model ref が見つからない",
                    raw_response={"inventory_count": len(inventory)},
                    provider_identity=self._provider_identity(ref),
                )
                continue
            results[ref] = ModelProbeResult(
                model_ref=ref,
                status=MODEL_AVAILABLE,
                detail="provider inventory で解決済み",
                raw_response=matched,
                provider_identity=self._provider_identity(ref),
            )
        return provider, results

    def pull(
        self,
        model_ref: str,
        on_progress: Callable[[PullProgress], None] | None = None,
    ) -> PullResult:
        """Ollama で model pull を実行する (TASK-00014-02)."""
        provider_identity = self._provider_identity(model_ref)
        status_snapshot = self.status()
        if status_snapshot.status != PROBE_REACHABLE:
            return PullResult(
                state="failed",
                detail=(
                    f"provider {status_snapshot.status}:"
                    f" {status_snapshot.detail}"
                ),
                raw_response=status_snapshot.raw_response,
                provider_identity=provider_identity,
                metadata={"failure_kind": FAILURE_PROVIDER_UNREACHABLE},
            )

        inventory_names = {
            str(item.get("name") or item.get("model"))
            for item in status_snapshot.inventory
            if isinstance(item, dict)
            and (item.get("name") is not None or item.get("model") is not None)
        }
        if model_ref in inventory_names:
            return PullResult(
                state="already_present",
                detail="provider inventory で既に利用可能",
                raw_response={
                    "inventory_count": len(inventory_names),
                    "model_ref": model_ref,
                },
                provider_identity=provider_identity,
                metadata={"inventory_count": len(inventory_names)},
            )

        url = f"{self._base_url()}/api/pull"
        req = urllib.request.Request(
            url,
            data=json.dumps({"model": model_ref}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        events: list[PullProgress] = []
        try:
            with urllib.request.urlopen(
                req,
                timeout=self.endpoint.timeout_seconds,
            ) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError as exc:
                        return PullResult(
                            state="failed",
                            detail=f"pull 進捗の JSON 解析失敗: {exc}",
                            raw_response={"line": line},
                            provider_identity=provider_identity,
                            progress=tuple(events),
                            metadata={
                                "failure_kind": FAILURE_MALFORMED_RESPONSE
                            },
                        )
                    event = PullProgress(
                        status=str(payload.get("status", "unknown")),
                        digest=(
                            None
                            if payload.get("digest") is None
                            else str(payload.get("digest"))
                        ),
                        total=(
                            int(payload["total"])
                            if isinstance(payload.get("total"), int)
                            else None
                        ),
                        completed=(
                            int(payload["completed"])
                            if isinstance(payload.get("completed"), int)
                            else None
                        ),
                        raw_response=payload,
                    )
                    events.append(event)
                    if on_progress is not None:
                        on_progress(event)
        except urllib.error.HTTPError as exc:
            detail_body = ""
            try:
                detail_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            return PullResult(
                state="failed",
                detail=f"HTTP {exc.code}: {detail_body[:200]}",
                raw_response={"http_status": exc.code, "body": detail_body},
                provider_identity=provider_identity,
                progress=tuple(events),
                metadata={"failure_kind": FAILURE_PROVIDER_RUNTIME},
            )
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            failure_kind = (
                FAILURE_TIMEOUT
                if isinstance(reason, TimeoutError)
                or "timed out" in str(reason).lower()
                else FAILURE_PROVIDER_UNREACHABLE
            )
            return PullResult(
                state="failed",
                detail=str(reason),
                raw_response={"error": str(reason)},
                provider_identity=provider_identity,
                progress=tuple(events),
                metadata={"failure_kind": failure_kind},
            )
        except TimeoutError as exc:
            return PullResult(
                state="failed",
                detail=str(exc),
                raw_response={"error": str(exc)},
                provider_identity=provider_identity,
                progress=tuple(events),
                metadata={"failure_kind": FAILURE_TIMEOUT},
            )

        if not events:
            return PullResult(
                state="failed",
                detail="pull 応答が空",
                raw_response={},
                provider_identity=provider_identity,
                metadata={"failure_kind": FAILURE_MALFORMED_RESPONSE},
            )

        final_status = events[-1].status
        state = "succeeded" if final_status == "success" else "failed"
        return PullResult(
            state=state,
            detail=final_status,
            raw_response=[event.raw_response for event in events],
            provider_identity=provider_identity,
            progress=tuple(events),
            metadata=(
                {}
                if state == "succeeded"
                else {"failure_kind": FAILURE_PROVIDER_RUNTIME}
            ),
        )

    def warmup(self, model_ref: str) -> WarmupResult:
        """空 prompt の generate で model をロードする (TASK-00014-02)."""
        provider_identity = self._provider_identity(model_ref)
        started = time.perf_counter()
        try:
            raw = self._request_json(
                "POST",
                "/api/generate",
                {"model": model_ref, "prompt": "", "stream": False},
            )
        except urllib.error.HTTPError as exc:
            detail_body = ""
            try:
                detail_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            failure_kind = (
                FAILURE_MODEL_NOT_FOUND
                if exc.code == 404
                else FAILURE_PROVIDER_RUNTIME
            )
            return WarmupResult(
                state="failed",
                detail=f"HTTP {exc.code}: {detail_body[:200]}",
                elapsed_seconds=time.perf_counter() - started,
                raw_response={"http_status": exc.code, "body": detail_body},
                provider_identity=provider_identity,
                metadata={"failure_kind": failure_kind},
            )
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            failure_kind = (
                FAILURE_TIMEOUT
                if isinstance(reason, TimeoutError)
                or "timed out" in str(reason).lower()
                else FAILURE_PROVIDER_UNREACHABLE
            )
            return WarmupResult(
                state="failed",
                detail=str(reason),
                elapsed_seconds=time.perf_counter() - started,
                raw_response={"error": str(reason)},
                provider_identity=provider_identity,
                metadata={"failure_kind": failure_kind},
            )
        except TimeoutError as exc:
            return WarmupResult(
                state="failed",
                detail=str(exc),
                elapsed_seconds=time.perf_counter() - started,
                raw_response={"error": str(exc)},
                provider_identity=provider_identity,
                metadata={"failure_kind": FAILURE_TIMEOUT},
            )
        except ValueError as exc:
            return WarmupResult(
                state="failed",
                detail=str(exc),
                elapsed_seconds=time.perf_counter() - started,
                raw_response={"error": str(exc)},
                provider_identity=provider_identity,
                metadata={"failure_kind": FAILURE_MALFORMED_RESPONSE},
            )

        elapsed = time.perf_counter() - started
        if not isinstance(raw, dict):
            return WarmupResult(
                state="failed",
                detail="warmup 応答が辞書でない",
                elapsed_seconds=elapsed,
                raw_response=raw,
                provider_identity=provider_identity,
                metadata={"failure_kind": FAILURE_MALFORMED_RESPONSE},
            )
        return WarmupResult(
            state="ready",
            detail="model load request completed",
            elapsed_seconds=elapsed,
            raw_response=raw,
            provider_identity=provider_identity,
            metadata={
                "done_reason": raw.get("done_reason"),
                "load_duration": raw.get("load_duration"),
                "total_duration": raw.get("total_duration"),
            },
        )

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        url = f"{self._base_url()}/api/generate"
        identity = self._provider_identity(request.model_ref)

        # PVD-00306 unsupported_request: provider に届ける前の事前検査.
        # Ollama が解釈できる範囲を逸脱した生成条件 (負の温度・0 以下の
        # max_tokens 等) は実行時検出 (HTTP 400) より早く落とす.
        unsupported = self.validate_request(request)
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
            input_tokens=(
                int(input_tokens)
                if isinstance(input_tokens, int)
                else None
            ),
            output_tokens=(
                int(output_tokens)
                if isinstance(output_tokens, int)
                else None
            ),
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
