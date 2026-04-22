"""task_id 00009-04, 00020-02: deterministic scorer と run 集計の確認。"""

from __future__ import annotations

import unittest

from local_llm_benchmark.benchmark.evaluation import (
    aggregate_run_metrics,
    build_request_snapshot,
    evaluate_record,
)
from local_llm_benchmark.benchmark.models import (
    BenchmarkPlan,
    BenchmarkRecord,
    GenerationSettings,
    InferenceResponse,
)
from local_llm_benchmark.config.models import ModelSelector
from local_llm_benchmark.prompts.models import EvaluationMetadata, PromptSpec
from local_llm_benchmark.registry.models import ModelSpec


class EvaluationHelpersTest(unittest.TestCase):
    def test_evaluate_record_for_all_categories(self) -> None:
        records = [
            _make_record(
                case_id="m1:classification",
                prompt_id="contact-routing-v1",
                prompt_category="classification",
                output_text='{"label": "請求"}',
                evaluation={
                    "reference_snapshot": {"label": "請求"},
                    "conditions": [
                        {
                            "metric_name": "accuracy",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "prediction_path": "label",
                                "label_space": ["請求", "技術サポート"],
                            },
                        }
                    ],
                },
            ),
            _make_record(
                case_id="m1:extraction",
                prompt_id="invoice-fields-v1",
                prompt_category="extraction",
                output_text=(
                    '{"invoice_number": "INV-2048", "due_date": "2026-05-15", '
                    '"amount_jpy": 12800}'
                ),
                evaluation={
                    "reference_snapshot": {
                        "invoice_number": "INV-2048",
                        "due_date": "2026-05-15",
                        "amount_jpy": 12800,
                    },
                    "conditions": [
                        {
                            "metric_name": "exact_match_rate",
                            "scorer_name": "exact_match_json_fields",
                            "scorer_version": "v1",
                            "reference_type": "json",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "required_fields": [
                                    "invoice_number",
                                    "due_date",
                                    "amount_jpy",
                                ]
                            },
                        },
                        {
                            "metric_name": "json_valid_rate",
                            "scorer_name": "json_valid",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "threshold": {"type": "min", "value": 1.0},
                            "metric_definition": {
                                "required_fields": ["invoice_number"]
                            },
                        },
                        {
                            "metric_name": "json_payload_valid_rate",
                            "scorer_name": "json_payload_valid",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        },
                        {
                            "metric_name": "payload_exact_match_rate",
                            "scorer_name": "payload_exact_match_json_fields",
                            "scorer_version": "v1",
                            "reference_type": "json",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "required_fields": [
                                    "invoice_number",
                                    "due_date",
                                    "amount_jpy",
                                ]
                            },
                        },
                    ],
                },
            ),
            _make_record(
                case_id="m1:rewrite",
                prompt_id="polite-rewrite-v1",
                prompt_category="rewrite",
                output_text="明日の会議資料は準備中ですので、少々お待ちください。",
                evaluation={
                    "output_contract_snapshot": {
                        "required_phrases": ["少々お待ちください"],
                        "forbidden_phrases": ["待って"],
                        "sentence_count": {"min": 1, "max": 1},
                    },
                    "conditions": [
                        {
                            "metric_name": "constraint_pass_rate",
                            "scorer_name": "constraint_pass",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        }
                    ],
                },
            ),
            _make_record(
                case_id="m1:summarization",
                prompt_id="meeting-notice-summary-v1",
                prompt_category="summarization",
                output_text=(
                    "顧客説明会は来週水曜14時開始に変更されます。資料は前日17時までに共有"
                    "フォルダへ提出し、会場参加が難しい場合は火曜正午までに担当へ連絡が必要"
                    "です。関係者は予定を更新してください。"
                ),
                evaluation={
                    "output_contract_snapshot": {
                        "length_range": {"min_chars": 80, "max_chars": 120}
                    },
                    "conditions": [
                        {
                            "metric_name": "length_compliance_rate",
                            "scorer_name": "length_compliance",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        }
                    ],
                },
            ),
            _make_record(
                case_id="m1:short-qa",
                prompt_id="support-hours-answer-v1",
                prompt_category="short_qa",
                output_text="17:00",
                evaluation={
                    "reference_snapshot": {"text": "17:00"},
                    "conditions": [
                        {
                            "metric_name": "exact_match_rate",
                            "scorer_name": "exact_match_text",
                            "scorer_version": "v1",
                            "reference_type": "text",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        }
                    ],
                },
            ),
            _make_record(
                case_id="m1:constrained-generation",
                prompt_id="followup-action-json-v1",
                prompt_category="constrained_generation",
                output_text=(
                    '{"channel": "メール", "priority": "high", '
                    '"action": "本日中に折り返し対応します"}'
                ),
                evaluation={
                    "expected_output_format": "json",
                    "output_contract_snapshot": {
                        "type": "json_object",
                        "required_keys": ["channel", "priority", "action"],
                        "allowed_keys": ["channel", "priority", "action"],
                        "required_phrases": ["high", "折り返し"],
                        "required_values": {"priority": "high"},
                        "field_types": {
                            "channel": "string",
                            "priority": "string",
                            "action": "string",
                        },
                    },
                    "conditions": [
                        {
                            "metric_name": "constraint_pass_rate",
                            "scorer_name": "constraint_pass",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        },
                        {
                            "metric_name": "format_valid_rate",
                            "scorer_name": "format_valid",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "threshold": {"type": "min", "value": 1.0},
                        },
                        {
                            "metric_name": "payload_format_valid_rate",
                            "scorer_name": "payload_format_valid",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        },
                        {
                            "metric_name": "payload_constraint_pass_rate",
                            "scorer_name": "payload_constraint_pass",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                        },
                    ],
                },
            ),
        ]

        rows = []
        for record in records:
            rows.extend(evaluate_record(record))

        self.assertEqual(12, len(rows))
        self.assertTrue(all(row["passed"] for row in rows))
        self.assertEqual(
            {
                "accuracy",
                "exact_match_rate",
                "json_valid_rate",
                "json_payload_valid_rate",
                "constraint_pass_rate",
                "length_compliance_rate",
                "format_valid_rate",
                "payload_exact_match_rate",
                "payload_format_valid_rate",
                "payload_constraint_pass_rate",
            },
            {row["metric_name"] for row in rows},
        )

    def test_payload_metrics_distinguish_single_fenced_json(self) -> None:
        extraction_rows = _rows_by_metric(
            evaluate_record(
                _make_auto_record(
                    case_id="m1:extraction:fenced",
                    prompt=_make_extraction_prompt(),
                    output_text=(
                        "```json\n"
                        '{"invoice_number": "INV-2048", '
                        '"due_date": "2026-05-15", '
                        '"amount_jpy": 12800}\n'
                        "```"
                    ),
                )
            )
        )
        self.assertEqual(False, extraction_rows["json_valid_rate"]["passed"])
        self.assertEqual(False, extraction_rows["exact_match_rate"]["passed"])
        self.assertEqual(
            True,
            extraction_rows["json_payload_valid_rate"]["passed"],
        )
        self.assertEqual(
            True,
            extraction_rows["payload_exact_match_rate"]["passed"],
        )

        constrained_rows = _rows_by_metric(
            evaluate_record(
                _make_auto_record(
                    case_id="m1:constrained:fenced",
                    prompt=_make_constrained_generation_prompt(),
                    output_text=(
                        "```json\n"
                        '{"channel": "メール", "priority": "high", '
                        '"action": "本日中に折り返し対応します"}\n'
                        "```"
                    ),
                )
            )
        )
        self.assertEqual(
            False,
            constrained_rows["format_valid_rate"]["passed"],
        )
        self.assertEqual(
            False,
            constrained_rows["constraint_pass_rate"]["passed"],
        )
        self.assertEqual(
            True,
            constrained_rows["payload_format_valid_rate"]["passed"],
        )
        self.assertEqual(
            True,
            constrained_rows["payload_constraint_pass_rate"]["passed"],
        )

    def test_payload_metrics_do_not_strip_prose_around_json(self) -> None:
        rows = _rows_by_metric(
            evaluate_record(
                _make_auto_record(
                    case_id="m1:extraction:prose",
                    prompt=_make_extraction_prompt(),
                    output_text=(
                        "回答です。\n"
                        "```json\n"
                        '{"invoice_number": "INV-2048", '
                        '"due_date": "2026-05-15", '
                        '"amount_jpy": 12800}\n'
                        "```"
                    ),
                )
            )
        )

        self.assertEqual(
            False,
            rows["json_payload_valid_rate"]["passed"],
        )
        self.assertEqual(
            False,
            rows["payload_exact_match_rate"]["passed"],
        )

    def test_aggregate_run_metrics(self) -> None:
        classification_records = [
            _make_record(
                case_id="m1:p1",
                prompt_id="contact-routing-v1",
                prompt_category="classification",
                output_text='{"label": "請求"}',
                evaluation={
                    "reference_snapshot": {"label": "請求"},
                    "conditions": [
                        {
                            "metric_name": "accuracy",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "prediction_path": "label",
                                "label_space": ["請求", "技術サポート"],
                            },
                        },
                        {
                            "metric_name": "macro_f1",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "macro_f1",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "prediction_path": "label",
                                "label_space": ["請求", "技術サポート"],
                            },
                        },
                    ],
                },
            ),
            _make_record(
                case_id="m1:p2",
                prompt_id="contact-routing-v1",
                prompt_category="classification",
                output_text='{"label": "請求"}',
                evaluation={
                    "reference_snapshot": {"label": "技術サポート"},
                    "conditions": [
                        {
                            "metric_name": "accuracy",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "prediction_path": "label",
                                "label_space": ["請求", "技術サポート"],
                            },
                        },
                        {
                            "metric_name": "macro_f1",
                            "scorer_name": "exact_match_label",
                            "scorer_version": "v1",
                            "reference_type": "label",
                            "aggregation": "macro_f1",
                            "evaluation_mode": "auto",
                            "metric_definition": {
                                "prediction_path": "label",
                                "label_space": ["請求", "技術サポート"],
                            },
                        },
                    ],
                },
            ),
            _make_record(
                case_id="m1:p3",
                prompt_id="invoice-fields-v1",
                prompt_category="extraction",
                output_text="not-json",
                evaluation={
                    "reference_snapshot": {"invoice_number": "INV-2048"},
                    "conditions": [
                        {
                            "metric_name": "json_valid_rate",
                            "scorer_name": "json_valid",
                            "scorer_version": "v1",
                            "reference_type": "none",
                            "aggregation": "mean",
                            "evaluation_mode": "auto",
                            "threshold": {"type": "min", "value": 1.0},
                            "metric_definition": {
                                "required_fields": ["invoice_number"]
                            },
                        }
                    ],
                },
            ),
        ]

        case_rows = []
        for record in classification_records:
            case_rows.extend(evaluate_record(record))

        payload = aggregate_run_metrics(
            run_id="run-agg",
            records=classification_records,
            case_evaluations=case_rows,
        )

        metrics_by_name = {
            (
                metric["scope"]["prompt_id"],
                metric["metric_name"],
            ): metric
            for metric in payload["metrics"]
        }
        self.assertAlmostEqual(
            0.5,
            metrics_by_name[("contact-routing-v1", "accuracy")]["value"],
        )
        self.assertAlmostEqual(
            0.333333,
            metrics_by_name[("contact-routing-v1", "macro_f1")]["value"],
            places=6,
        )
        self.assertEqual(
            False,
            metrics_by_name[
                ("invoice-fields-v1", "json_valid_rate")
            ]["passed"],
        )

    def test_aggregate_run_metrics_includes_payload_metrics(self) -> None:
        records = [
            _make_auto_record(
                case_id="m1:extraction:fenced",
                prompt=_make_extraction_prompt(),
                output_text=(
                    "```json\n"
                    '{"invoice_number": "INV-2048", '
                    '"due_date": "2026-05-15", '
                    '"amount_jpy": 12800}\n'
                    "```"
                ),
            ),
            _make_auto_record(
                case_id="m1:constrained:fenced",
                prompt=_make_constrained_generation_prompt(),
                output_text=(
                    "```json\n"
                    '{"channel": "メール", "priority": "high", '
                    '"action": "本日中に折り返し対応します"}\n'
                    "```"
                ),
            ),
        ]

        case_rows = []
        for record in records:
            case_rows.extend(evaluate_record(record))

        payload = aggregate_run_metrics(
            run_id="run-agg-payload",
            records=records,
            case_evaluations=case_rows,
        )

        metrics_by_name = {
            (
                metric["scope"]["prompt_id"],
                metric["metric_name"],
            ): metric
            for metric in payload["metrics"]
        }
        self.assertAlmostEqual(
            0.0,
            metrics_by_name[("invoice-fields-v1", "json_valid_rate")][
                "value"
            ],
        )
        self.assertAlmostEqual(
            1.0,
            metrics_by_name[
                ("invoice-fields-v1", "json_payload_valid_rate")
            ]["value"],
        )
        self.assertAlmostEqual(
            1.0,
            metrics_by_name[
                ("invoice-fields-v1", "payload_exact_match_rate")
            ]["value"],
        )
        self.assertEqual(
            False,
            metrics_by_name[("invoice-fields-v1", "json_valid_rate")][
                "passed"
            ],
        )
        self.assertIsNone(
            metrics_by_name[
                ("invoice-fields-v1", "json_payload_valid_rate")
            ]["passed"],
        )
        self.assertAlmostEqual(
            0.0,
            metrics_by_name[
                ("followup-action-json-v1", "format_valid_rate")
            ]["value"],
        )
        self.assertAlmostEqual(
            1.0,
            metrics_by_name[
                ("followup-action-json-v1", "payload_format_valid_rate")
            ]["value"],
        )
        self.assertAlmostEqual(
            1.0,
            metrics_by_name[
                (
                    "followup-action-json-v1",
                    "payload_constraint_pass_rate",
                )
            ]["value"],
        )


def _make_record(
    *,
    case_id: str,
    prompt_id: str,
    prompt_category: str,
    output_text: str,
    evaluation: dict[str, object],
) -> BenchmarkRecord:
    return BenchmarkRecord(
        run_id="run-1",
        case_id=case_id,
        model_key="model-a",
        prompt_id=prompt_id,
        request_snapshot={
            "prompt_category": prompt_category,
            "evaluation": evaluation,
        },
        response=InferenceResponse(
            output_text=output_text,
            raw_response={"raw": output_text},
        ),
    )


def _make_auto_record(
    *,
    case_id: str,
    prompt: PromptSpec,
    output_text: str,
) -> BenchmarkRecord:
    model = ModelSpec(
        model_key="model-a",
        provider_id="provider-a",
        provider_model_name="model-a",
    )
    plan = BenchmarkPlan(
        run_id="run-1",
        suite_id="suite-1",
        model_selector=ModelSelector(
            explicit_model_keys=(model.model_key,),
            provider_id=model.provider_id,
        ),
        default_generation=GenerationSettings(
            temperature=0.0,
            top_p=0.95,
            max_tokens=128,
            seed=7,
        ),
        trace_metadata={"task_id": "00020-02"},
    )
    request_snapshot = build_request_snapshot(
        plan=plan,
        model=model,
        prompt=prompt,
        generation=plan.default_generation,
        prompt_bindings={},
    )
    return BenchmarkRecord(
        run_id=plan.run_id,
        case_id=case_id,
        model_key=model.model_key,
        prompt_id=prompt.prompt_id,
        request_snapshot=request_snapshot,
        response=InferenceResponse(
            output_text=output_text,
            raw_response={"raw": output_text},
        ),
    )


def _make_extraction_prompt() -> PromptSpec:
    return PromptSpec(
        prompt_id="invoice-fields-v1",
        version="1",
        category="extraction",
        title="invoice fields",
        description="task_id 00020-02: payload metric extraction prompt",
        system_message="JSON のみを返してください。",
        user_message="請求情報を抽出してください。",
        recommended_generation=GenerationSettings(
            temperature=0.0,
            max_tokens=128,
            seed=7,
        ),
        evaluation_metadata=EvaluationMetadata(
            primary_metric="exact_match_rate",
            secondary_metrics=(
                "json_valid_rate",
                "json_payload_valid_rate",
                "payload_exact_match_rate",
            ),
            reference_type="json",
            scorer="exact_match_json_fields",
            expected_output_format="json",
        ),
        output_contract={
            "required_fields": [
                "invoice_number",
                "due_date",
                "amount_jpy",
            ],
            "field_types": {
                "invoice_number": "string",
                "due_date": "string",
                "amount_jpy": "integer",
            },
        },
        metadata={
            "task_id": "00020-02",
            "evaluation_reference": {
                "invoice_number": "INV-2048",
                "due_date": "2026-05-15",
                "amount_jpy": 12800,
            },
        },
    )


def _make_constrained_generation_prompt() -> PromptSpec:
    return PromptSpec(
        prompt_id="followup-action-json-v1",
        version="1",
        category="constrained_generation",
        title="followup action",
        description=(
            "task_id 00020-02: payload metric constrained_generation prompt"
        ),
        system_message="JSON のみを返してください。",
        user_message="フォローアップアクションを JSON で返してください。",
        recommended_generation=GenerationSettings(
            temperature=0.0,
            max_tokens=128,
            seed=7,
        ),
        evaluation_metadata=EvaluationMetadata(
            primary_metric="constraint_pass_rate",
            secondary_metrics=(
                "format_valid_rate",
                "payload_format_valid_rate",
                "payload_constraint_pass_rate",
            ),
            reference_type="none",
            scorer="constraint_pass",
            expected_output_format="json",
        ),
        output_contract={
            "type": "json_object",
            "required_keys": ["channel", "priority", "action"],
            "allowed_keys": ["channel", "priority", "action"],
            "required_phrases": ["high", "折り返し"],
            "required_values": {"priority": "high"},
            "field_types": {
                "channel": "string",
                "priority": "string",
                "action": "string",
            },
        },
        metadata={"task_id": "00020-02"},
    )


def _rows_by_metric(
    rows: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {
        str(row["metric_name"]): row
        for row in rows
    }


if __name__ == "__main__":
    unittest.main()
