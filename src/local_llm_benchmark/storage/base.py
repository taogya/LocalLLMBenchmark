"""task_id 00001-03, 00009-04: 保存境界の抽象。"""

from __future__ import annotations

from typing import Any, Protocol

from local_llm_benchmark.benchmark.models import BenchmarkRecord


class ResultSink(Protocol):
    def write(self, record: BenchmarkRecord) -> None:
        ...

    def write_case_evaluations(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        ...

    def write_run_metrics(self, payload: dict[str, Any]) -> None:
        ...

    def close(self) -> None:
        ...
