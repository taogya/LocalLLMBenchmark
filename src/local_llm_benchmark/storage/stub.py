"""task_id 00001-03, 00009-04: no-op / in-memory の保存スタブ。"""

from __future__ import annotations

from typing import Any

from local_llm_benchmark.benchmark.models import BenchmarkRecord


class NoOpResultSink:
    def write(self, record: BenchmarkRecord) -> None:
        _ = record

    def write_case_evaluations(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        _ = rows

    def write_run_metrics(self, payload: dict[str, Any]) -> None:
        _ = payload

    def close(self) -> None:
        return None


class MemoryResultSink:
    def __init__(self) -> None:
        self.records: list[BenchmarkRecord] = []
        self.case_evaluations: list[dict[str, Any]] = []
        self.run_metrics: dict[str, Any] | None = None
        self.closed = False

    def write(self, record: BenchmarkRecord) -> None:
        self.records.append(record)

    def write_case_evaluations(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        self.case_evaluations.extend(rows)

    def write_run_metrics(self, payload: dict[str, Any]) -> None:
        self.run_metrics = dict(payload)

    def close(self) -> None:
        self.closed = True
