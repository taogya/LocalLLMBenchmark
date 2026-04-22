"""task_id 00006-03, 00009-04, 00020-02: 評価 snapshot と deterministic scorer。"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
import re
from typing import Any
import unicodedata

from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    BenchmarkRecord,
    GenerationSettings,
    InferenceResponse,
)
from local_llm_benchmark.prompts.models import PromptSpec
from local_llm_benchmark.registry.models import ModelSpec

_MISSING = object()
_SENTENCE_SPLIT_PATTERN = re.compile(r"[。.!?！？]+")
_PAYLOAD_PREPROCESSING = (
    "strip_outer_whitespace",
    "unwrap_single_fenced_block",
)
_SINGLE_FENCED_BLOCK_PATTERN = re.compile(
    r"\A(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)\r?\n"
    r"(?P<body>[\s\S]*?)\r?\n(?P=fence)\Z"
)


def build_request_snapshot(
    *,
    plan: BenchmarkPlan,
    model: ModelSpec,
    prompt: PromptSpec,
    generation: GenerationSettings,
    prompt_bindings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "suite_id": plan.suite_id,
        "provider_id": model.provider_id,
        "provider_model_name": model.provider_model_name,
        "prompt_category": prompt.category,
        "generation": generation.to_snapshot(),
        "prompt_bindings": dict(prompt_bindings),
        "trace_metadata": dict(plan.trace_metadata),
        "prompt_snapshot": _build_prompt_snapshot(prompt),
        "evaluation": _build_evaluation_snapshot(prompt),
    }


def evaluate_record(record: BenchmarkRecord) -> list[dict[str, Any]]:
    if record.response is None:
        return []

    evaluation = _as_mapping(record.request_snapshot.get("evaluation"))
    conditions = evaluation.get("conditions", [])
    if not isinstance(conditions, list):
        return []

    case_rows: list[dict[str, Any]] = []
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        if condition.get("evaluation_mode") != "auto":
            continue
        case_rows.append(
            _evaluate_condition(
                record=record,
                evaluation=evaluation,
                condition=condition,
            )
        )
    return case_rows


def aggregate_run_metrics(
    *,
    run_id: str,
    records: list[BenchmarkRecord],
    case_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    condition_index = _build_condition_index(records)
    grouped_rows: dict[tuple[str, str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for row in case_evaluations:
        key = (
            str(row.get("model_key", "")),
            str(row.get("prompt_id", "")),
            str(row.get("prompt_category", "")),
            str(row.get("metric_name", "")),
        )
        grouped_rows[key].append(row)

    metrics: list[dict[str, Any]] = []
    for scope_key in sorted(grouped_rows):
        rows = grouped_rows[scope_key]
        if not rows:
            continue
        condition = condition_index.get(
            (
                str(rows[0].get("case_id", "")),
                str(rows[0].get("metric_name", "")),
            )
        )
        if condition is None:
            continue
        value = _aggregate_case_rows(rows, condition)
        threshold = deepcopy(condition.get("threshold"))
        metrics.append(
            {
                "scope": {
                    "model_key": scope_key[0],
                    "prompt_id": scope_key[1],
                    "prompt_category": scope_key[2],
                },
                "metric_name": scope_key[3],
                "scorer_name": condition.get("scorer_name"),
                "scorer_version": condition.get("scorer_version"),
                "aggregation": condition.get("aggregation"),
                "value": value,
                "threshold": threshold,
                "passed": _evaluate_run_threshold(value, threshold),
                "sample_count": len(rows),
                "evaluation_mode": condition.get("evaluation_mode"),
            }
        )

    return {
        "schema_version": "run-metrics.v1",
        "run_id": run_id,
        "metrics": metrics,
    }


def _build_prompt_snapshot(prompt: PromptSpec) -> dict[str, Any]:
    return {
        "version": prompt.version,
        "category": prompt.category,
        "tags": list(prompt.tags),
        "evaluation_metadata_snapshot": {
            "primary_metric": prompt.evaluation_metadata.primary_metric,
            "secondary_metrics": list(
                prompt.evaluation_metadata.secondary_metrics
            ),
            "reference_type": prompt.evaluation_metadata.reference_type,
            "scorer": prompt.evaluation_metadata.scorer,
            "difficulty": prompt.evaluation_metadata.difficulty,
            "language": prompt.evaluation_metadata.language,
            "expected_output_format": (
                prompt.evaluation_metadata.expected_output_format
            ),
        },
    }


def _build_evaluation_snapshot(prompt: PromptSpec) -> dict[str, Any]:
    return {
        "expected_output_format": (
            prompt.evaluation_metadata.expected_output_format
        ),
        "output_contract_snapshot": deepcopy(prompt.output_contract),
        "reference_snapshot": deepcopy(
            prompt.metadata.get("evaluation_reference", {})
        ),
        "conditions": _resolve_evaluation_conditions(prompt),
    }


def _resolve_evaluation_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    category = prompt.category
    if category == "classification":
        return _classification_conditions(prompt)
    if category == "extraction":
        return _extraction_conditions(prompt)
    if category == "rewrite":
        return _rewrite_conditions(prompt)
    if category == "summarization":
        return _summarization_conditions(prompt)
    if category == "short_qa":
        return _short_qa_conditions(prompt)
    if category == "constrained_generation":
        return _constrained_generation_conditions(prompt)
    return [_fallback_condition(prompt)]


def _classification_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    metric_definition = {
        "prediction_path": prompt.output_contract.get(
            "prediction_path",
            "label",
        ),
        "label_space": list(prompt.output_contract.get("label_space", [])),
        "normalization": ["nfkc", "strip"],
    }
    common = {
        "scorer_name": "exact_match_label",
        "scorer_version": "v1",
        "reference_type": "label",
        "threshold": None,
        "pass_rule": "case_exact_match",
        "metric_definition": metric_definition,
        "evaluation_mode": "auto",
    }
    return [
        {
            **common,
            "metric_name": "accuracy",
            "aggregation": "mean",
        },
        {
            **common,
            "metric_name": "macro_f1",
            "aggregation": "macro_f1",
        },
    ]


def _extraction_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    required_fields = prompt.output_contract.get(
        "required_fields",
        prompt.output_contract.get("required_keys", []),
    )
    metric_definition = {
        "required_fields": list(required_fields),
        "field_types": deepcopy(prompt.output_contract.get("field_types", {})),
        "normalization": ["nfkc", "strip"],
    }
    payload_metric_definition = deepcopy(metric_definition)
    payload_metric_definition["preprocessing"] = list(
        _PAYLOAD_PREPROCESSING
    )
    return [
        {
            "metric_name": "exact_match_rate",
            "scorer_name": "exact_match_json_fields",
            "scorer_version": "v1",
            "reference_type": "json",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_json_exact_match",
            "metric_definition": metric_definition,
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "json_valid_rate",
            "scorer_name": "json_valid",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": {"type": "min", "value": 1.0},
            "pass_rule": "run_all_cases_must_be_valid_json",
            "metric_definition": {
                "required_fields": list(required_fields),
            },
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "json_payload_valid_rate",
            "scorer_name": "json_payload_valid",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_payload_must_be_valid_json_object",
            "metric_definition": deepcopy(payload_metric_definition),
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "payload_exact_match_rate",
            "scorer_name": "payload_exact_match_json_fields",
            "scorer_version": "v1",
            "reference_type": "json",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_payload_json_exact_match",
            "metric_definition": deepcopy(payload_metric_definition),
            "evaluation_mode": "auto",
        },
    ]


def _rewrite_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    return [
        {
            "metric_name": "constraint_pass_rate",
            "scorer_name": "constraint_pass",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_all_constraints_must_pass",
            "metric_definition": {
                "constraint_ids": list(
                    prompt.output_contract.get("constraint_ids", [])
                ),
            },
            "evaluation_mode": "auto",
        }
    ]


def _summarization_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    length_range = deepcopy(prompt.output_contract.get("length_range", {}))
    return [
        {
            "metric_name": "length_compliance_rate",
            "scorer_name": "length_compliance",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": (
                {
                    "type": "range",
                    "min": length_range.get("min_chars"),
                    "max": length_range.get("max_chars"),
                    "unit": length_range.get("unit", "chars"),
                }
                if length_range
                else None
            ),
            "pass_rule": "case_within_length_range",
            "metric_definition": length_range,
            "evaluation_mode": "auto",
        }
    ]


def _short_qa_conditions(prompt: PromptSpec) -> list[dict[str, Any]]:
    return [
        {
            "metric_name": "exact_match_rate",
            "scorer_name": "exact_match_text",
            "scorer_version": "v1",
            "reference_type": "text",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_exact_match",
            "metric_definition": {"normalization": ["nfkc", "strip"]},
            "evaluation_mode": "auto",
        }
    ]


def _constrained_generation_conditions(
    prompt: PromptSpec,
) -> list[dict[str, Any]]:
    metric_definition = {
        "constraint_ids": list(
            prompt.output_contract.get("constraint_ids", [])
        ),
        "required_keys": list(prompt.output_contract.get("required_keys", [])),
        "allowed_keys": list(prompt.output_contract.get("allowed_keys", [])),
    }
    payload_metric_definition = deepcopy(metric_definition)
    payload_metric_definition["preprocessing"] = list(
        _PAYLOAD_PREPROCESSING
    )
    return [
        {
            "metric_name": "constraint_pass_rate",
            "scorer_name": "constraint_pass",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_all_constraints_must_pass",
            "metric_definition": metric_definition,
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "format_valid_rate",
            "scorer_name": "format_valid",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": {"type": "min", "value": 1.0},
            "pass_rule": "run_all_cases_must_match_format",
            "metric_definition": metric_definition,
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "payload_format_valid_rate",
            "scorer_name": "payload_format_valid",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_payload_must_match_format",
            "metric_definition": deepcopy(payload_metric_definition),
            "evaluation_mode": "auto",
        },
        {
            "metric_name": "payload_constraint_pass_rate",
            "scorer_name": "payload_constraint_pass",
            "scorer_version": "v1",
            "reference_type": "none",
            "aggregation": "mean",
            "threshold": None,
            "pass_rule": "case_payload_constraints_must_pass",
            "metric_definition": deepcopy(payload_metric_definition),
            "evaluation_mode": "auto",
        },
    ]


def _fallback_condition(prompt: PromptSpec) -> dict[str, Any]:
    return {
        "metric_name": prompt.evaluation_metadata.primary_metric,
        "scorer_name": prompt.evaluation_metadata.scorer,
        "scorer_version": "v1",
        "reference_type": prompt.evaluation_metadata.reference_type,
        "aggregation": "mean",
        "threshold": None,
        "pass_rule": "unspecified",
        "metric_definition": {},
        "evaluation_mode": (
            "manual"
            if prompt.evaluation_metadata.scorer.startswith("manual")
            else "auto"
        ),
    }


def _evaluate_condition(
    *,
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    scorer_name = condition.get("scorer_name")
    if scorer_name == "exact_match_label":
        result = _score_exact_match_label(record, evaluation, condition)
    elif scorer_name == "exact_match_text":
        result = _score_exact_match_text(record, evaluation)
    elif scorer_name == "exact_match_json_fields":
        result = _score_exact_match_json_fields(record, evaluation, condition)
    elif scorer_name == "payload_exact_match_json_fields":
        result = _score_payload_exact_match_json_fields(
            record,
            evaluation,
            condition,
        )
    elif scorer_name == "json_valid":
        result = _score_json_valid(record)
    elif scorer_name == "json_payload_valid":
        result = _score_json_payload_valid(record)
    elif scorer_name == "constraint_pass":
        result = _score_constraint_pass(record, evaluation)
    elif scorer_name == "payload_constraint_pass":
        result = _score_payload_constraint_pass(record, evaluation)
    elif scorer_name == "length_compliance":
        result = _score_length_compliance(record, evaluation)
    elif scorer_name == "format_valid":
        result = _score_format_valid(record, evaluation)
    elif scorer_name == "payload_format_valid":
        result = _score_payload_format_valid(record, evaluation)
    else:
        result = {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": None,
            "details": {"error": f"unsupported_scorer:{scorer_name}"},
        }

    return {
        "schema_version": "case-evaluation.v1",
        "run_id": record.run_id,
        "case_id": record.case_id,
        "model_key": record.model_key,
        "prompt_id": record.prompt_id,
        "prompt_category": record.request_snapshot.get("prompt_category"),
        "metric_name": condition.get("metric_name"),
        "scorer_name": condition.get("scorer_name"),
        "scorer_version": condition.get("scorer_version"),
        "reference_type": condition.get("reference_type"),
        "evaluation_mode": condition.get("evaluation_mode"),
        "score": result["score"],
        "passed": result["passed"],
        "normalized_prediction": result["normalized_prediction"],
        "normalized_reference": result["normalized_reference"],
        "details": result["details"],
    }


def _score_exact_match_label(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    reference = _normalize_string(
        _as_mapping(evaluation.get("reference_snapshot")).get("label")
    )
    prediction_path = _as_mapping(condition.get("metric_definition")).get(
        "prediction_path",
        "label",
    )
    prediction, parse_error = _extract_prediction_value(
        response.output_text,
        str(prediction_path),
    )
    normalized_prediction = _normalize_scalar(prediction)
    details: dict[str, Any] = {}
    if parse_error is not None:
        details["parse_error"] = parse_error
    score = 1.0 if normalized_prediction == reference else 0.0
    return {
        "score": score,
        "passed": score == 1.0,
        "normalized_prediction": normalized_prediction,
        "normalized_reference": reference,
        "details": details,
    }


def _score_exact_match_text(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    reference = _normalize_string(
        _as_mapping(evaluation.get("reference_snapshot")).get("text")
    )
    prediction = _normalize_string(response.output_text)
    score = 1.0 if prediction == reference else 0.0
    return {
        "score": score,
        "passed": score == 1.0,
        "normalized_prediction": prediction,
        "normalized_reference": reference,
        "details": {},
    }


def _score_exact_match_json_fields(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_exact_match_json_fields_text(
        response.output_text,
        evaluation,
        condition,
    )


def _score_payload_exact_match_json_fields(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_exact_match_json_fields_text(
        _normalize_json_payload_text(response.output_text),
        evaluation,
        condition,
    )


def _score_exact_match_json_fields_text(
    output_text: str,
    evaluation: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, Any]:
    metric_definition = _as_mapping(condition.get("metric_definition"))
    required_fields = list(metric_definition.get("required_fields", []))
    reference_snapshot = _as_mapping(evaluation.get("reference_snapshot"))
    normalized_reference = {
        field: _normalize_scalar(reference_snapshot.get(field))
        for field in required_fields
    }
    parsed_json, parse_error = _parse_json(output_text)
    details: dict[str, Any] = {}
    if parse_error is not None:
        details["parse_error"] = parse_error
        details["missing_fields"] = required_fields
        return {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": normalized_reference,
            "details": details,
        }
    if not isinstance(parsed_json, dict):
        details["parse_error"] = "json_object_required"
        details["missing_fields"] = required_fields
        return {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": normalized_reference,
            "details": details,
        }

    normalized_prediction: dict[str, Any] = {}
    missing_fields: list[str] = []
    mismatched_fields: dict[str, dict[str, Any]] = {}
    for field in required_fields:
        if field not in parsed_json:
            missing_fields.append(field)
            continue
        normalized_prediction[field] = _normalize_scalar(parsed_json[field])
        expected_value = normalized_reference[field]
        actual_value = normalized_prediction[field]
        if actual_value != expected_value:
            mismatched_fields[field] = {
                "expected": expected_value,
                "actual": actual_value,
            }

    if missing_fields:
        details["missing_fields"] = missing_fields
    if mismatched_fields:
        details["mismatched_fields"] = mismatched_fields
    score = 1.0 if not missing_fields and not mismatched_fields else 0.0
    return {
        "score": score,
        "passed": score == 1.0,
        "normalized_prediction": normalized_prediction,
        "normalized_reference": normalized_reference,
        "details": details,
    }


def _score_json_valid(record: BenchmarkRecord) -> dict[str, Any]:
    response = _require_response(record)
    return _score_json_valid_text(response.output_text)


def _score_json_payload_valid(record: BenchmarkRecord) -> dict[str, Any]:
    response = _require_response(record)
    return _score_json_object_valid_text(
        _normalize_json_payload_text(response.output_text)
    )


def _score_json_valid_text(output_text: str) -> dict[str, Any]:
    parsed_json, parse_error = _parse_json(output_text)
    details: dict[str, Any] = {}
    if parse_error is not None:
        details["parse_error"] = parse_error
        return {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": None,
            "details": details,
        }
    return {
        "score": 1.0,
        "passed": True,
        "normalized_prediction": _normalize_scalar(parsed_json),
        "normalized_reference": None,
        "details": details,
    }


def _score_json_object_valid_text(output_text: str) -> dict[str, Any]:
    parsed_json, parse_error = _parse_json(output_text)
    details: dict[str, Any] = {}
    if parse_error is not None:
        details["parse_error"] = parse_error
        return {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": None,
            "details": details,
        }
    if not isinstance(parsed_json, dict):
        details["parse_error"] = "json_object_required"
        return {
            "score": 0.0,
            "passed": False,
            "normalized_prediction": None,
            "normalized_reference": None,
            "details": details,
        }
    return {
        "score": 1.0,
        "passed": True,
        "normalized_prediction": _normalize_scalar(parsed_json),
        "normalized_reference": None,
        "details": details,
    }


def _score_constraint_pass(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_constraint_pass_text(response.output_text, evaluation)


def _score_payload_constraint_pass(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_constraint_pass_text(
        _normalize_json_payload_text(response.output_text),
        evaluation,
    )


def _score_constraint_pass_text(
    output_text: str,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    output_contract = _as_mapping(evaluation.get("output_contract_snapshot"))
    normalized_text = _normalize_string(output_text) or ""
    failed_constraints: list[str] = []
    details: dict[str, Any] = {}

    for phrase in _as_string_list(output_contract.get("required_phrases")):
        normalized_phrase = _normalize_string(phrase) or ""
        if normalized_phrase not in normalized_text:
            failed_constraints.append(f"required_phrase:{phrase}")

    for phrase in _as_string_list(output_contract.get("forbidden_phrases")):
        normalized_phrase = _normalize_string(phrase) or ""
        if normalized_phrase in normalized_text:
            failed_constraints.append(f"forbidden_phrase:{phrase}")

    sentence_count = _as_mapping(output_contract.get("sentence_count"))
    if sentence_count:
        observed_count = _count_sentences(output_text)
        details["observed_sentence_count"] = observed_count
        minimum = sentence_count.get("min")
        maximum = sentence_count.get("max")
        if isinstance(minimum, int) and observed_count < minimum:
            failed_constraints.append("sentence_count")
        if isinstance(maximum, int) and observed_count > maximum:
            failed_constraints.append("sentence_count")

    required_values = _as_mapping(output_contract.get("required_values"))
    if required_values:
        parsed_json, parse_error = _parse_json(output_text)
        if parse_error is not None or not isinstance(parsed_json, dict):
            failed_constraints.append("required_values")
            details["required_values_error"] = (
                parse_error or "json_object_required"
            )
        else:
            value_mismatches: dict[str, dict[str, Any]] = {}
            for field_name, expected_value in required_values.items():
                actual_value = parsed_json.get(field_name, _MISSING)
                if actual_value is _MISSING:
                    value_mismatches[str(field_name)] = {
                        "expected": _normalize_scalar(expected_value),
                        "actual": None,
                    }
                    continue
                normalized_expected = _normalize_scalar(expected_value)
                normalized_actual = _normalize_scalar(actual_value)
                if normalized_actual != normalized_expected:
                    value_mismatches[str(field_name)] = {
                        "expected": normalized_expected,
                        "actual": normalized_actual,
                    }
            if value_mismatches:
                failed_constraints.append("required_values")
                details["value_mismatches"] = value_mismatches

    details["failed_constraints"] = failed_constraints
    score = 1.0 if not failed_constraints else 0.0
    return {
        "score": score,
        "passed": score == 1.0,
        "normalized_prediction": normalized_text,
        "normalized_reference": None,
        "details": details,
    }


def _score_length_compliance(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    output_contract = _as_mapping(evaluation.get("output_contract_snapshot"))
    length_range = _as_mapping(output_contract.get("length_range"))
    observed_length = len(response.output_text.strip())
    minimum = length_range.get("min_chars")
    maximum = length_range.get("max_chars")
    passed = True
    if isinstance(minimum, int) and observed_length < minimum:
        passed = False
    if isinstance(maximum, int) and observed_length > maximum:
        passed = False
    return {
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "normalized_prediction": observed_length,
        "normalized_reference": None,
        "details": {
            "observed_length": observed_length,
            "min_chars": minimum,
            "max_chars": maximum,
        },
    }


def _score_format_valid(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_format_valid_text(response.output_text, evaluation)


def _score_payload_format_valid(
    record: BenchmarkRecord,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    response = _require_response(record)
    return _score_format_valid_text(
        _normalize_json_payload_text(response.output_text),
        evaluation,
    )


def _score_format_valid_text(
    output_text: str,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    output_contract = _as_mapping(evaluation.get("output_contract_snapshot"))
    expected_output_format = evaluation.get("expected_output_format")
    format_errors: list[str] = []
    details: dict[str, Any] = {}
    normalized_prediction: Any = None

    if (
        expected_output_format == "json"
        or output_contract.get("type") == "json_object"
    ):
        parsed_json, parse_error = _parse_json(output_text)
        if parse_error is not None:
            format_errors.append("invalid_json")
            details["parse_error"] = parse_error
        elif not isinstance(parsed_json, dict):
            format_errors.append("json_object_required")
        else:
            normalized_prediction = _normalize_scalar(parsed_json)
            required_keys = _as_string_list(
                output_contract.get("required_keys")
            )
            missing_keys = [
                key for key in required_keys if key not in parsed_json
            ]
            if missing_keys:
                format_errors.append("missing_keys")
                details["missing_keys"] = missing_keys

            allowed_keys = _as_string_list(output_contract.get("allowed_keys"))
            if allowed_keys:
                unexpected_keys = [
                    key for key in parsed_json if key not in allowed_keys
                ]
                if unexpected_keys:
                    format_errors.append("unexpected_keys")
                    details["unexpected_keys"] = unexpected_keys

            field_types = _as_mapping(output_contract.get("field_types"))
            if field_types:
                type_errors: dict[str, dict[str, Any]] = {}
                for field_name, declared_type in field_types.items():
                    if field_name not in parsed_json:
                        continue
                    if not _matches_declared_type(
                        parsed_json[field_name],
                        str(declared_type),
                    ):
                        type_errors[str(field_name)] = {
                            "expected": declared_type,
                            "actual": _json_type_name(parsed_json[field_name]),
                        }
                if type_errors:
                    format_errors.append("field_type_mismatch")
                    details["type_errors"] = type_errors
    elif expected_output_format == "bullet_list":
        lines = [
            line.strip()
            for line in output_text.splitlines()
            if line.strip()
        ]
        normalized_prediction = lines
        if not lines or not all(
            line.startswith(("-", "*", "・")) for line in lines
        ):
            format_errors.append("bullet_list_required")
    else:
        normalized_prediction = _normalize_string(output_text)
        if not normalized_prediction:
            format_errors.append("empty_text")

    details["format_errors"] = format_errors
    score = 1.0 if not format_errors else 0.0
    return {
        "score": score,
        "passed": score == 1.0,
        "normalized_prediction": normalized_prediction,
        "normalized_reference": None,
        "details": details,
    }


def _build_condition_index(
    records: list[BenchmarkRecord],
) -> dict[tuple[str, str], dict[str, Any]]:
    condition_index: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        evaluation = _as_mapping(record.request_snapshot.get("evaluation"))
        conditions = evaluation.get("conditions", [])
        if not isinstance(conditions, list):
            continue
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            metric_name = condition.get("metric_name")
            if not isinstance(metric_name, str):
                continue
            condition_index[(record.case_id, metric_name)] = condition
    return condition_index


def _aggregate_case_rows(
    rows: list[dict[str, Any]],
    condition: dict[str, Any],
) -> float:
    aggregation = condition.get("aggregation")
    if aggregation == "macro_f1":
        return round(_compute_macro_f1(rows, condition), 6)
    if not rows:
        return 0.0
    total = sum(float(row.get("score", 0.0)) for row in rows)
    return round(total / len(rows), 6)


def _compute_macro_f1(
    rows: list[dict[str, Any]],
    condition: dict[str, Any],
) -> float:
    metric_definition = _as_mapping(condition.get("metric_definition"))
    labels = [
        label
        for label in metric_definition.get("label_space", [])
        if isinstance(label, str)
    ]
    if not labels:
        derived_labels = {
            _normalize_string(row.get("normalized_reference"))
            for row in rows
        }
        derived_labels.update(
            _normalize_string(row.get("normalized_prediction")) for row in rows
        )
        labels = sorted(label for label in derived_labels if label)
    if not labels:
        return 0.0

    f1_scores: list[float] = []
    for label in labels:
        true_positive = 0
        false_positive = 0
        false_negative = 0
        for row in rows:
            prediction = _normalize_string(row.get("normalized_prediction"))
            reference = _normalize_string(row.get("normalized_reference"))
            if prediction == label and reference == label:
                true_positive += 1
            elif prediction == label and reference != label:
                false_positive += 1
            elif prediction != label and reference == label:
                false_negative += 1
        precision = (
            true_positive / (true_positive + false_positive)
            if (true_positive + false_positive)
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if (true_positive + false_negative)
            else 0.0
        )
        if precision == 0.0 and recall == 0.0:
            f1_scores.append(0.0)
        else:
            f1_scores.append((2 * precision * recall) / (precision + recall))
    return sum(f1_scores) / len(f1_scores)


def _evaluate_run_threshold(
    value: float,
    threshold: Any,
) -> bool | None:
    if not isinstance(threshold, dict):
        return None
    threshold_type = threshold.get("type")
    if threshold_type == "min":
        threshold_value = threshold.get("value")
        if isinstance(threshold_value, (int, float)):
            return value >= float(threshold_value)
    if threshold_type == "range":
        return None
    return None


def _extract_prediction_value(
    output_text: str,
    prediction_path: str,
) -> tuple[Any, str | None]:
    parsed_json, parse_error = _parse_json(output_text)
    if parse_error is not None:
        return output_text, parse_error
    if not isinstance(parsed_json, dict):
        return output_text, "json_object_required"
    value = _lookup_path(parsed_json, prediction_path)
    if value is _MISSING:
        return output_text, f"prediction_path_not_found:{prediction_path}"
    return value, None


def _lookup_path(payload: dict[str, Any], prediction_path: str) -> Any:
    current: Any = payload
    for segment in [part for part in prediction_path.split(".") if part]:
        if not isinstance(current, dict) or segment not in current:
            return _MISSING
        current = current[segment]
    return current


def _normalize_json_payload_text(text: str) -> str:
    stripped = text.strip()
    fence_match = _SINGLE_FENCED_BLOCK_PATTERN.fullmatch(stripped)
    if fence_match is None:
        return stripped
    return fence_match.group("body").strip()


def _parse_json(text: str) -> tuple[Any, str | None]:
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, (
            f"{exc.msg} at line {exc.lineno} column {exc.colno}"
        )


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return _normalize_string(value)
    if isinstance(value, dict):
        return {
            str(key): _normalize_scalar(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_scalar(item) for item in value]
    return value


def _normalize_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return unicodedata.normalize("NFKC", value).strip()


def _count_sentences(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    fragments = [
        fragment.strip()
        for fragment in _SENTENCE_SPLIT_PATTERN.split(stripped)
        if fragment.strip()
    ]
    return len(fragments) if fragments else 1


def _matches_declared_type(value: Any, declared_type: str) -> bool:
    if declared_type == "string":
        return isinstance(value, str)
    if declared_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared_type == "boolean":
        return isinstance(value, bool)
    if declared_type == "array":
        return isinstance(value, list)
    if declared_type == "object":
        return isinstance(value, dict)
    return True


def _json_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _require_response(record: BenchmarkRecord) -> InferenceResponse:
    if record.response is None:
        raise ValueError("auto evaluation には response が必要です。")
    return record.response


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
