"""task_id 00006-03, 00009-04: JSONL ベースの ResultSink 実装。"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    BenchmarkRecord,
    InferenceResponse,
)

_SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


class JsonlResultSink:
    def __init__(self, output_root: Path, plan: BenchmarkPlan) -> None:
        self._plan = plan
        self.run_dir = output_root / plan.run_id
        self._raw_dir = self.run_dir / "raw"
        self._records_path = self.run_dir / "records.jsonl"
        self._case_evaluations_path = self.run_dir / "case-evaluations.jsonl"
        self._run_metrics_path = self.run_dir / "run-metrics.json"
        self._manifest_path = self.run_dir / "manifest.json"
        self._record_count = 0
        self._case_evaluation_count = 0
        self._run_metrics_written = False
        self._closed = False

        if self.run_dir.exists():
            raise ValueError(
                f"run_id '{plan.run_id}' の結果ディレクトリが既に存在します。"
                "別の run_id を指定してください。"
            )

        self.run_dir.mkdir(parents=True, exist_ok=False)
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        self._records_stream = self._records_path.open("w", encoding="utf-8")
        self._case_evaluations_stream = self._case_evaluations_path.open(
            "w",
            encoding="utf-8",
        )
        self._write_manifest(status="running")

    def write(self, record: BenchmarkRecord) -> None:
        if self._closed:
            raise RuntimeError("close() 後に ResultSink へ write はできません。")

        serialized_record = {
            "schema_version": "benchmark-record.v1",
            "run_id": record.run_id,
            "case_id": record.case_id,
            "model_key": record.model_key,
            "prompt_id": record.prompt_id,
            "request_snapshot": dict(record.request_snapshot),
            "response": self._serialize_response(record),
            "error": record.error,
        }
        self._records_stream.write(
            json.dumps(serialized_record, ensure_ascii=False) + "\n"
        )
        self._records_stream.flush()
        self._record_count += 1
        self._write_manifest(status="running")

    def write_case_evaluations(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        if self._closed:
            raise RuntimeError("close() 後に ResultSink へ write はできません。")
        for row in rows:
            self._case_evaluations_stream.write(
                json.dumps(row, ensure_ascii=False) + "\n"
            )
            self._case_evaluation_count += 1
        self._case_evaluations_stream.flush()

    def write_run_metrics(self, payload: dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("close() 後に ResultSink へ write はできません。")
        self._run_metrics_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._run_metrics_written = True

    def close(self) -> None:
        if self._closed:
            return
        self._records_stream.close()
        self._case_evaluations_stream.close()
        if not self._run_metrics_written:
            self.write_run_metrics(
                {
                    "schema_version": "run-metrics.v1",
                    "run_id": self._plan.run_id,
                    "metrics": [],
                }
            )
        self._write_manifest(status="completed")
        self._closed = True

    def _serialize_response(
        self,
        record: BenchmarkRecord,
    ) -> dict[str, Any] | None:
        response = record.response
        if response is None:
            return None
        raw_response_path = self._write_raw_response(record, response)
        payload: dict[str, Any] = {
            "output_text": response.output_text,
            "raw_response_path": str(
                raw_response_path.relative_to(self.run_dir)
            ),
        }
        if response.usage is not None:
            payload["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        if response.latency_ms is not None:
            payload["latency_ms"] = response.latency_ms
        if response.finish_reason is not None:
            payload["finish_reason"] = response.finish_reason
        return payload

    def _write_raw_response(
        self,
        record: BenchmarkRecord,
        response: InferenceResponse,
    ) -> Path:
        raw_path = self._raw_dir / self._build_raw_file_name(record)
        raw_payload = {
            "run_id": record.run_id,
            "case_id": record.case_id,
            "model_key": record.model_key,
            "prompt_id": record.prompt_id,
            "provider_id": record.request_snapshot.get("provider_id"),
            "provider_model_name": record.request_snapshot.get(
                "provider_model_name"
            ),
            "provider_metadata": dict(response.provider_metadata),
            "raw_response": response.raw_response,
        }
        raw_path.write_text(
            json.dumps(raw_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return raw_path

    def _build_raw_file_name(self, record: BenchmarkRecord) -> str:
        safe_case_key = _SAFE_NAME_PATTERN.sub("-", record.case_id).strip("-")
        if not safe_case_key:
            safe_case_key = "case"
        return f"{self._record_count + 1:05d}-{safe_case_key}.json"

    def _write_manifest(self, *, status: str) -> None:
        manifest = {
            "schema_version": "result-sink.v1",
            "run_id": self._plan.run_id,
            "suite_id": self._plan.suite_id,
            "status": status,
            "record_count": self._record_count,
            "layout": {
                "records": "records.jsonl",
                "raw_dir": "raw",
                "case_evaluations": "case-evaluations.jsonl",
                "run_metrics": "run-metrics.json",
            },
            "plan_snapshot": {
                "model_selector": {
                    "explicit_model_keys": list(
                        self._plan.model_selector.explicit_model_keys
                    ),
                    "include_tags": list(
                        self._plan.model_selector.include_tags
                    ),
                    "provider_id": self._plan.model_selector.provider_id,
                },
                "prompt_set_ids": list(self._plan.prompt_set_ids),
                "prompt_ids": list(self._plan.prompt_ids),
                "default_generation": (
                    self._plan.default_generation.to_snapshot()
                ),
                "trace_metadata": dict(self._plan.trace_metadata),
            },
        }
        self._manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
