"""Report Renderer (TASK-00007-02, COMP-00012).

Result Store 由来の Run / Comparison データを Markdown に変換する.

設計依拠:
- COMP-00012: Run 表示は単一モデルの集計表、Comparison 表示はモデル横断の
  ランキング表 (品質重視 / 速度重視 / 統合) を主体とする。
- DAT-00106: 数値は CaseAggregation ないしモデルサマリ由来のみ。Trial
  個別値には触らない。
- SCR-00810: 絶対秒は人間可読出力に常に併記する。
- CLI-00201: 機械可読 (JSON) は Result Store の正準データを最小加工で出力
  し、人間可読 (Markdown) はその派生形とする (本モジュールは Markdown
  のみ担当)。
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


# ---- 共通フォーマッタ -----------------------------------------------------


def _fmt_float(value: float | None, fmt: str = "{:.4f}") -> str:
    if value is None:
        return "-"
    return fmt.format(value)


def _fmt_seconds(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f} s"


# ---- Run レポート ---------------------------------------------------------


def render_run_markdown(
    meta: Mapping[str, Any],
    aggregation: Mapping[str, Any],
) -> str:
    """単一 Run の Markdown レポートを生成する (FLW-00002).

    ランキングは含まない (COMP-00012 / FLW-00002 注記)。
    """
    run_id = meta.get("run_id", "(unknown)")
    model = meta.get("model_candidate") or {}
    started_at = meta.get("started_at", "-")
    n_trials = meta.get("n_trials", "-")
    task_profiles = meta.get("task_profiles") or []
    cond = meta.get("generation_conditions") or {}
    summary = aggregation.get("run_summary") or {}
    cases = aggregation.get("case_aggregations") or []

    lines: list[str] = []
    lines.append(f"# Run レポート: {run_id}")
    lines.append("")
    lines.append("## 概要")
    lines.append("")
    lines.append(f"- 開始時刻: {started_at}")
    lines.append(
        f"- Model Candidate: {model.get('name', '-')}"
        f" (provider={model.get('provider_kind', '-')},"
        f" model_ref={model.get('provider_model_ref', '-')})"
    )
    lines.append(f"- Task Profiles: {', '.join(map(str, task_profiles)) or '-'}")
    lines.append(f"- 試行回数 (n): {n_trials}")
    lines.append(
        f"- 生成条件: temperature={cond.get('temperature')},"
        f" seed={cond.get('seed')}, max_tokens={cond.get('max_tokens')}"
    )
    if meta.get("aborted"):
        lines.append(f"- 中断: {meta.get('abort_reason')}")
    lines.append("")
    lines.append("## モデルサマリ")
    lines.append("")
    lines.append("| 指標 | 値 |")
    lines.append("| --- | --- |")
    lines.append(f"| 品質スコア mean | {_fmt_float(summary.get('score_mean'))} |")
    lines.append(f"| 応答時間 mean | {_fmt_seconds(summary.get('latency_mean'))} |")
    lines.append(
        f"| 出力トークン mean | {_fmt_float(summary.get('output_tokens_mean'), '{:.2f}')} |"
    )
    lines.append(f"| 成功 Trial 数 | {summary.get('success_trials', 0)} |")
    lines.append(f"| 失敗 Trial 数 | {summary.get('failure_trials', 0)} |")
    lines.append("")
    lines.append("## Case 別集計")
    lines.append("")
    lines.append(
        "| Task Profile | Case | n | score mean | score p50 | score p95 |"
        " latency mean | latency p95 | failures |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for c in cases:
        lines.append(
            "| {tp} | {case} | {n} | {sm} | {sp50} | {sp95} |"
            " {lm} | {lp95} | {fc} |".format(
                tp=c.get("task_profile_name", "-"),
                case=c.get("case_name", "-"),
                n=c.get("n", 0),
                sm=_fmt_float(c.get("score_mean")),
                sp50=_fmt_float(c.get("score_p50")),
                sp95=_fmt_float(c.get("score_p95")),
                lm=_fmt_seconds(c.get("latency_mean")),
                lp95=_fmt_seconds(c.get("latency_p95")),
                fc=c.get("failure_count", 0),
            )
        )
    lines.append("")
    return "\n".join(lines)


# ---- Comparison レポート --------------------------------------------------


def _ranking_table(items: Sequence[Mapping[str, Any]], value_label: str) -> list[str]:
    out = [
        f"| 順位 | Model | Run ID | {value_label} |",
        "| --- | --- | --- | --- |",
    ]
    for it in items:
        v = it.get("value")
        if value_label.startswith("latency") or value_label.startswith("応答時間"):
            value_str = _fmt_seconds(v)
        else:
            value_str = _fmt_float(v)
        out.append(
            f"| {it.get('rank', '-')} | {it.get('model_name', '-')} |"
            f" {it.get('run_id', '-')} | {value_str} |"
        )
    return out


def render_comparison_markdown(comparison_payload: Mapping[str, Any]) -> str:
    """Comparison の Markdown レポートを生成する (FUN-00308 / FLW-00006).

    `comparison_payload` は ResultStore.load_comparison が返す JSON 構造を
    想定する (Comparison + 内包 ComparisonReport)。
    """
    cmp_id = comparison_payload.get("comparison_id", "(unknown)")
    created_at = comparison_payload.get("created_at", "-")
    run_ids = comparison_payload.get("run_ids") or []
    weights = comparison_payload.get("weights") or {}
    axis_default = comparison_payload.get("ranking_axis_default", "integrated")
    report = comparison_payload.get("report") or {}
    per_model = report.get("per_model") or []
    task_profiles = report.get("task_profile_names") or []

    lines: list[str] = []
    lines.append(f"# Comparison レポート: {cmp_id}")
    lines.append("")
    # NFR-00004: 人間可読出力の先頭にランキング表が現れること.
    # ランキング 3 軸 (SCR-00802/00803/00804) を最上段に配置する.
    lines.append("## ランキング: 品質重視 (SCR-00802)")
    lines.append("")
    lines.extend(_ranking_table(report.get("ranking_quality") or [], "quality mean"))
    lines.append("")
    lines.append("## ランキング: 速度重視 (SCR-00803)")
    lines.append("")
    lines.extend(
        _ranking_table(report.get("ranking_speed") or [], "応答時間 mean")
    )
    lines.append("")
    lines.append("## ランキング: 統合 (SCR-00804)")
    lines.append("")
    lines.extend(
        _ranking_table(report.get("ranking_integrated") or [], "integrated score")
    )
    lines.append("")
    lines.append("## 概要")
    lines.append("")
    lines.append(f"- 作成時刻: {created_at}")
    lines.append(f"- 入力 Run 識別子 ({len(run_ids)} 件): {', '.join(run_ids)}")
    lines.append(
        f"- 共通 Task Profile セット: {', '.join(map(str, task_profiles)) or '-'}"
    )
    lines.append(
        f"- 重み (SCR-00806/00807): w_quality={weights.get('w_quality')},"
        f" w_speed={weights.get('w_speed')}"
    )
    lines.append(f"- 既定ランキング軸: {axis_default}")
    lines.append("")
    lines.append("## モデル別サマリ")
    lines.append("")
    lines.append(
        "| Model | Run ID | quality mean | quality p50 | latency mean |"
        " latency p95 | output tokens mean | speed subscore | integrated |"
        " success | failure |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for m in per_model:
        lines.append(
            "| {name} | {rid} | {qm} | {qp50} | {lm} | {lp95} | {otm} |"
            " {sp} | {ig} | {ok} | {ng} |".format(
                name=m.get("model_name", "-"),
                rid=m.get("run_id", "-"),
                qm=_fmt_float(m.get("quality_mean")),
                qp50=_fmt_float(m.get("quality_p50")),
                lm=_fmt_seconds(m.get("latency_mean")),
                lp95=_fmt_seconds(m.get("latency_p95")),
                otm=_fmt_float(m.get("output_tokens_mean"), "{:.2f}"),
                sp=_fmt_float(m.get("speed_subscore")),
                ig=_fmt_float(m.get("integrated_score")),
                ok=m.get("success_trials", 0),
                ng=m.get("failure_trials", 0),
            )
        )
    lines.append("")
    return "\n".join(lines)
