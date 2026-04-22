"""task_id 00011-02, 00015-02: run-metrics の report helper。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class ReportMetricRow:
    model_key: str
    prompt_category: str
    prompt_id: str
    metric_name: str
    value: float
    threshold: Any
    passed: bool | None
    sample_count: int

    @property
    def scope_key(self) -> tuple[str, str, str]:
        return (self.model_key, self.prompt_category, self.prompt_id)

    @property
    def comparison_key(self) -> tuple[str, str, str, str]:
        return (
            self.model_key,
            self.prompt_category,
            self.prompt_id,
            self.metric_name,
        )


@dataclass(frozen=True)
class SingleRunReport:
    run_id: str
    suite_id: str
    run_dir: Path
    record_count: int
    metric_rows: tuple[ReportMetricRow, ...]

    @property
    def unique_scope_count(self) -> int:
        return len({row.scope_key for row in self.metric_rows})


@dataclass(frozen=True)
class ComparisonMetricRow:
    model_key: str
    prompt_category: str
    prompt_id: str
    metric_name: str
    run_rows: tuple[ReportMetricRow | None, ...]

    @property
    def has_missing(self) -> bool:
        return any(row is None for row in self.run_rows)

    @property
    def is_different(self) -> bool:
        baseline_state = _comparison_state(self.run_rows[0])
        return any(
            _comparison_state(row) != baseline_state
            for row in self.run_rows[1:]
        )

    @property
    def threshold_text(self) -> str:
        threshold_texts = {
            _format_threshold(row.threshold)
            for row in self.run_rows
            if row is not None
        }
        if not threshold_texts:
            return "-"
        if len(threshold_texts) == 1:
            return next(iter(threshold_texts))
        return "varies"


@dataclass(frozen=True)
class ComparisonReport:
    reports: tuple[SingleRunReport, ...]
    differing_rows: tuple[ComparisonMetricRow, ...]
    identical_row_count: int

    @property
    def suite_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(report.suite_id for report in self.reports))

    @property
    def has_suite_id_mismatch(self) -> bool:
        return len(self.suite_ids) > 1

    @property
    def has_missing_rows(self) -> bool:
        return any(row.has_missing for row in self.differing_rows)


def render_run_report(run_dir: Path | str) -> str:
    report = load_run_report(run_dir)
    lines = [
        f"run_id: {report.run_id}",
        f"suite_id: {report.suite_id}",
        f"run_dir: {report.run_dir}",
        f"records: {report.record_count}",
        f"metric_rows: {len(report.metric_rows)}",
        (
            "legend: records=manifest.record_count, "
            "scope=model_key | prompt_category | prompt_id, "
            "n=sample_count, passed=n/a when run threshold is not "
            "evaluated"
        ),
    ]
    for row in report.metric_rows:
        lines.append(
            "- "
            f"{row.model_key} | {row.prompt_category} | {row.prompt_id} | "
            f"{row.metric_name} | value={row.value:.3f} | "
            f"threshold={_format_threshold(row.threshold)} | "
            f"passed={_format_passed(row.passed)} | n={row.sample_count}"
        )
    if report.unique_scope_count != report.record_count:
        lines.append(
            "note: "
            f"manifest.record_count={report.record_count}, "
            f"metric scopes={report.unique_scope_count}. "
            "sample_count は各 metric 行に寄与した case 数で、実行失敗"
            "または auto 評価対象外 record は含まない。"
        )
    return "\n".join(lines)


def render_comparison_report(run_dirs: Sequence[Path | str]) -> str:
    comparison = load_comparison_report(run_dirs)
    baseline_report = comparison.reports[0]
    lines = [
        f"baseline_run_id: {baseline_report.run_id}",
    ]
    if not comparison.has_suite_id_mismatch:
        lines.append(f"suite_id: {baseline_report.suite_id}")
    lines.extend(
        [
            (
                "compare_run_ids: "
                + ", ".join(report.run_id for report in comparison.reports[1:])
            ),
            f"run_count: {len(comparison.reports)}",
            f"differing_rows: {len(comparison.differing_rows)}",
            f"identical_rows_omitted: {comparison.identical_row_count}",
            (
                "legend: row_key=model_key | prompt_category | prompt_id | "
                "metric_name, base=先頭の --run-dir, delta=value-base.value, "
                "n=sample_count, pass/fail は strict gate の結果, "
                "passed=n/a は threshold 未評価, missing は row 不在"
            ),
            (
                "note: json_valid_rate / format_valid_rate は raw JSON-only "
                "contract を見る strict gate、constraint_pass_rate は "
                "exact lexical / structural contract を見る strict gate "
                "であり、semantic quality、自然な rewrite 品質、wrapper "
                "除去後の payload correctness は表さない。"
            ),
        ]
    )
    if comparison.has_suite_id_mismatch:
        lines.append(
            "note: suite_id mismatch: "
            + ", ".join(comparison.suite_ids)
            + ". compare は row_key=model_key | prompt_category | prompt_id | "
            "metric_name で揃え、suite_id は header note としてのみ扱う。"
        )
    if comparison.has_missing_rows:
        lines.append(
            "note: missing は run error、auto 評価対象外、suite / plan 差分"
            "などで row が存在しないことを表す。"
        )
    for row in comparison.differing_rows:
        lines.append(_render_comparison_row(row, comparison.reports))
    return "\n".join(lines)


def load_comparison_report(
    run_dirs: Sequence[Path | str],
) -> ComparisonReport:
    normalized_run_dirs = _normalize_comparison_run_dirs(run_dirs)
    reports = tuple(
        load_run_report(run_dir) for run_dir in normalized_run_dirs
    )
    _validate_unique_run_ids(reports)
    indexed_rows = tuple(_index_metric_rows(report) for report in reports)
    comparison_rows = tuple(
        ComparisonMetricRow(
            model_key=row_key[0],
            prompt_category=row_key[1],
            prompt_id=row_key[2],
            metric_name=row_key[3],
            run_rows=tuple(index.get(row_key) for index in indexed_rows),
        )
        for row_key in sorted(
            _collect_all_row_keys(indexed_rows),
            key=_sort_row_key,
        )
    )
    differing_rows = tuple(row for row in comparison_rows if row.is_different)
    return ComparisonReport(
        reports=reports,
        differing_rows=differing_rows,
        identical_row_count=len(comparison_rows) - len(differing_rows),
    )


def load_run_report(run_dir: Path | str) -> SingleRunReport:
    normalized_run_dir = Path(run_dir)
    manifest = _load_json_object(normalized_run_dir / "manifest.json")
    run_metrics = _load_json_object(normalized_run_dir / "run-metrics.json")
    manifest_run_id = _require_str(manifest, "run_id", "manifest.json")
    run_metrics_run_id = _require_str(
        run_metrics,
        "run_id",
        "run-metrics.json",
    )
    if run_metrics_run_id != manifest_run_id:
        raise ValueError(
            "manifest.json と run-metrics.json の run_id が一致しません。"
        )
    metric_rows = tuple(
        sorted(
            (
                _parse_metric_row(metric, index)
                for index, metric in enumerate(
                    _require_list(
                        run_metrics,
                        "metrics",
                        "run-metrics.json",
                    )
                )
            ),
            key=lambda row: (row.model_key, row.prompt_id, row.metric_name),
        )
    )
    return SingleRunReport(
        run_id=manifest_run_id,
        suite_id=_require_str(manifest, "suite_id", "manifest.json"),
        run_dir=normalized_run_dir,
        record_count=_require_int(manifest, "record_count", "manifest.json"),
        metric_rows=metric_rows,
    )


def _normalize_comparison_run_dirs(
    run_dirs: Sequence[Path | str],
) -> tuple[Path, ...]:
    if len(run_dirs) < 2:
        raise ValueError("compare には少なくとも 2 つの --run-dir が必要です。")
    normalized_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for run_dir in run_dirs:
        normalized_path = Path(run_dir).expanduser().resolve()
        if normalized_path in seen_paths:
            raise ValueError(
                "compare の --run-dir に重複パスがあります: "
                f"{normalized_path}"
            )
        seen_paths.add(normalized_path)
        normalized_paths.append(normalized_path)
    return tuple(normalized_paths)


def _validate_unique_run_ids(reports: Sequence[SingleRunReport]) -> None:
    seen_run_ids: dict[str, Path] = {}
    for report in reports:
        previous_run_dir = seen_run_ids.get(report.run_id)
        if previous_run_dir is not None:
            raise ValueError(
                "compare の run_id が重複しています: "
                f"{report.run_id} ({previous_run_dir} / {report.run_dir})"
            )
        seen_run_ids[report.run_id] = report.run_dir


def _index_metric_rows(
    report: SingleRunReport,
) -> dict[tuple[str, str, str, str], ReportMetricRow]:
    return {row.comparison_key: row for row in report.metric_rows}


def _collect_all_row_keys(
    indexed_rows: Sequence[dict[tuple[str, str, str, str], ReportMetricRow]],
) -> set[tuple[str, str, str, str]]:
    row_keys: set[tuple[str, str, str, str]] = set()
    for row_index in indexed_rows:
        row_keys.update(row_index)
    return row_keys


def _sort_row_key(
    row_key: tuple[str, str, str, str],
) -> tuple[str, str, str, str]:
    model_key, prompt_category, prompt_id, metric_name = row_key
    return (model_key, prompt_id, metric_name, prompt_category)


def _render_comparison_row(
    row: ComparisonMetricRow,
    reports: Sequence[SingleRunReport],
) -> str:
    baseline_row = row.run_rows[0]
    parts = [
        row.model_key,
        row.prompt_category,
        row.prompt_id,
        row.metric_name,
        f"threshold={row.threshold_text}",
        f"base={_format_comparison_value(baseline_row)}",
    ]
    for report, current_row in zip(reports[1:], row.run_rows[1:]):
        parts.append(
            f"{report.run_id}={_format_comparison_value(current_row)}"
        )
        parts.append(f"delta={_format_delta(baseline_row, current_row)}")
    parts.append(f"base_pass={_format_comparison_passed(baseline_row)}")
    for report, current_row in zip(reports[1:], row.run_rows[1:]):
        parts.append(
            f"{report.run_id}_pass={_format_comparison_passed(current_row)}"
        )
    parts.append(f"base_n={_format_comparison_sample_count(baseline_row)}")
    for report, current_row in zip(reports[1:], row.run_rows[1:]):
        parts.append(
            f"{report.run_id}_n={_format_comparison_sample_count(current_row)}"
        )
    return "- " + " | ".join(parts)


def _comparison_state(
    row: ReportMetricRow | None,
) -> tuple[bool, float | None, int | None, bool | None, str | None]:
    if row is None:
        return (True, None, None, None, None)
    return (
        False,
        row.value,
        row.sample_count,
        row.passed,
        _format_threshold(row.threshold),
    )


def _format_comparison_value(row: ReportMetricRow | None) -> str:
    if row is None:
        return "missing"
    return f"{row.value:.3f}"


def _format_delta(
    baseline_row: ReportMetricRow | None,
    current_row: ReportMetricRow | None,
) -> str:
    if baseline_row is None or current_row is None:
        return "n/a"
    return f"{current_row.value - baseline_row.value:+.3f}"


def _format_comparison_passed(row: ReportMetricRow | None) -> str:
    if row is None:
        return "missing"
    return _format_passed(row.passed)


def _format_comparison_sample_count(row: ReportMetricRow | None) -> str:
    if row is None:
        return "missing"
    return str(row.sample_count)


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{path.name} が見つかりません。")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path.name} の JSON が不正です: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} の JSON top-level は object 必須です。")
    return payload


def _parse_metric_row(payload: Any, index: int) -> ReportMetricRow:
    row_context = f"run-metrics.json の metrics[{index}]"
    if not isinstance(payload, dict):
        raise ValueError(f"{row_context} は object 必須です。")
    scope = _require_object(payload, "scope", row_context)
    return ReportMetricRow(
        model_key=_require_str(scope, "model_key", f"{row_context}.scope"),
        prompt_category=_require_str(
            scope,
            "prompt_category",
            f"{row_context}.scope",
        ),
        prompt_id=_require_str(scope, "prompt_id", f"{row_context}.scope"),
        metric_name=_require_str(payload, "metric_name", row_context),
        value=_require_number(payload, "value", row_context),
        threshold=_require_key(payload, "threshold", row_context),
        passed=_require_passed(payload, "passed", row_context),
        sample_count=_require_int(payload, "sample_count", row_context),
    )


def _require_key(payload: dict[str, Any], key: str, context: str) -> Any:
    if key not in payload:
        raise KeyError(f"{context} に '{key}' がありません。")
    return payload[key]


def _require_object(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> dict[str, Any]:
    value = _require_key(payload, key, context)
    if not isinstance(value, dict):
        raise ValueError(f"{context} の '{key}' は object 必須です。")
    return value


def _require_list(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = _require_key(payload, key, context)
    if not isinstance(value, list):
        raise ValueError(f"{context} の '{key}' は array 必須です。")
    return value


def _require_str(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> str:
    value = _require_key(payload, key, context)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} の '{key}' は空でない文字列必須です。")
    return value


def _require_int(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> int:
    value = _require_key(payload, key, context)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{context} の '{key}' は整数必須です。")
    return value


def _require_number(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> float:
    value = _require_key(payload, key, context)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{context} の '{key}' は数値必須です。")
    return float(value)


def _require_passed(
    payload: dict[str, Any],
    key: str,
    context: str,
) -> bool | None:
    value = _require_key(payload, key, context)
    if value is None or isinstance(value, bool):
        return value
    raise ValueError(f"{context} の '{key}' は bool または null 必須です。")


def _format_threshold(threshold: Any) -> str:
    if threshold is None:
        return "-"
    if not isinstance(threshold, dict):
        return "-"
    threshold_type = threshold.get("type")
    if threshold_type == "min":
        value = threshold.get("value")
        if _is_number(value):
            return f">={_format_min_threshold_number(float(value))}"
        return "-"
    if threshold_type == "range":
        minimum = threshold.get("min")
        maximum = threshold.get("max")
        if _is_number(minimum) and _is_number(maximum):
            range_text = (
                f"{_format_range_threshold_number(float(minimum))}"
                f"-{_format_range_threshold_number(float(maximum))}"
            )
            unit = threshold.get("unit")
            if isinstance(unit, str) and unit:
                return f"{range_text} {unit}"
            return range_text
    return "-"


def _format_passed(passed: bool | None) -> str:
    if passed is True:
        return "pass"
    if passed is False:
        return "fail"
    return "n/a"


def _format_min_threshold_number(value: float) -> str:
    if value.is_integer():
        return f"{value:.1f}"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_range_threshold_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
