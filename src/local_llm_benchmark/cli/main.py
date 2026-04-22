"""CLI Entry (TASK-00007-01 / TASK-00007-02 / TASK-00007-03, COMP-00001).

サブコマンド:
- run         CLI-00106
- compare     CLI-00107
- report      CLI-00102
- comparisons CLI-00108
- list        CLI-00103 (Phase 3)
- runs        CLI-00104 (Phase 3)
- check       CLI-00105 (Phase 3)

設計依拠:
- CLI-00203 進捗 (NFR-00501) は標準エラーへ、結果は標準出力へ
- CLI-00204 出力先指定はそのまま渡し、内容を加工しない
- CLI-00301..00306 終了コード分類
- argparse 自身が出すユーザー入力誤り (--help を除く) は CLI-00302 として
  扱う。SystemExit を捕捉して終了コードを正規化する.
- COMP-00010 / COMP-00011 / COMP-00012 への委譲
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from ..config import (
    ConfigurationError,
    assemble_run_plan,
    check_bundle,
    check_comparison,
    load_comparison_config,
    load_config_bundle,
    load_run_config,
)
from ..models import ComparisonWeights
from ..orchestration import ComparisonError, RunComparator, RunCoordinator
from ..reporting import render_comparison_markdown, render_run_markdown
from ..scoring import known_scorer_names
from ..storage import ResultStore


# 終了コード (CLI-00301..00306)
EXIT_SUCCESS = 0                       # CLI-00301
EXIT_USER_INPUT_ERROR = 2              # CLI-00302
EXIT_CONFIGURATION_ERROR = 3           # CLI-00303
EXIT_RUNTIME_ERROR = 4                 # CLI-00304
EXIT_PARTIAL_FAILURE = 5               # CLI-00305
EXIT_COMPARISON_INCOMPLETE = 6         # CLI-00306 (将来用に予約)


# ---- パーサ構築 -----------------------------------------------------------


_EPILOG = """\
使用例:
  # 1 Run = 1 Model のベンチマーク実行 (CLI-00106)
  local-llm-benchmark run --config-dir ./cfg --run-config ./run.toml \\
      --store-root ./results

  # 2 件以上の Run を束ねて比較 (CLI-00107)
  local-llm-benchmark compare --store-root ./results \\
      --run-id <ID-A> --run-id <ID-B>

  # Run / Comparison の Markdown レポート (CLI-00102)
  local-llm-benchmark report --store-root ./results --run-id <ID>

  # 設定の事前検証 (CLI-00105)
  local-llm-benchmark check --config-dir ./cfg
"""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-llm-benchmark",
        description=(
            "ローカル LLM ベンチマーク本体 (v1.0.0)。"
            "ユーザー PC・用途で最適なローカルモデルを選ぶ意思決定を支援する。"
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
        title="サブコマンド",
        metavar="<command>",
    )

    # ---- run (CLI-00106) ------------------------------------------------
    run_p = sub.add_parser(
        "run",
        help="1 Run = 1 Model のベンチマークを実行する (CLI-00106)",
        description=(
            "指定 Task Profile 群 × 1 件の Model Candidate を実行し、"
            "Run 識別子を返す (FUN-00207)。"
        ),
        epilog=(
            "例: local-llm-benchmark run --config-dir ./cfg "
            "--run-config ./run.toml --store-root ./results"
        ),
    )
    run_p.add_argument(
        "--config-dir", required=True, type=Path,
        help="ユーザー設定ディレクトリ (task_profiles/, model_candidates.toml, providers.toml)",
    )
    run_p.add_argument(
        "--run-config", required=True, type=Path,
        help="Run 設定 TOML (CFG-00107)",
    )
    run_p.add_argument(
        "--store-root", type=Path, default=None,
        help="Result Store のルート。未指定時は run-config の store_root か `./results`",
    )

    # ---- compare (CLI-00107) -------------------------------------------
    cmp_p = sub.add_parser(
        "compare",
        help="2 件以上の Run を束ねて Comparison を生成する (CLI-00107)",
        description=(
            "2 件以上の Run 識別子からモデル横断ランキング "
            "(品質重視 / 速度重視 / 統合) を生成する (FUN-00308)。"
        ),
        epilog=(
            "例: local-llm-benchmark compare --store-root ./results "
            "--run-id <ID-A> --run-id <ID-B> --axis integrated"
        ),
    )
    cmp_p.add_argument(
        "--store-root", required=True, type=Path,
        help="Result Store のルート (Run 識別子の解決元)",
    )
    cmp_p.add_argument(
        "--run-id", action="append", default=[],
        help="比較対象の Run 識別子。2 回以上指定するか --comparison-config を使う",
    )
    cmp_p.add_argument(
        "--comparison-config", type=Path, default=None,
        help="Comparison 設定 TOML (CFG-00207)。CLI 引数が優先される",
    )
    cmp_p.add_argument(
        "--axis", choices=("quality", "speed", "integrated"), default=None,
        help="既定ランキング軸。未指定時は設定 or `integrated`",
    )
    cmp_p.add_argument(
        "--w-quality", type=float, default=None,
        help="品質重み上書き (SCR-00808)。既定 SCR-00806=0.7",
    )
    cmp_p.add_argument(
        "--w-speed", type=float, default=None,
        help="速度重み上書き (SCR-00808)。既定 SCR-00807=0.3",
    )

    # ---- report (CLI-00102) --------------------------------------------
    rpt_p = sub.add_parser(
        "report",
        help="Run または Comparison の Markdown レポートを出力する (CLI-00102)",
        description=(
            "Result Store の Run または Comparison を読み出し、Markdown 形式で"
            " レポートを出力する。Run レポートにランキングは含まれない (CLI-00102)。"
        ),
    )
    rpt_p.add_argument(
        "--store-root", required=True, type=Path,
        help="Result Store のルート",
    )
    grp = rpt_p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--run-id", help="表示する Run 識別子 (FLW-00002)")
    grp.add_argument(
        "--comparison-id",
        help="表示する Comparison 識別子 (FUN-00308 / FLW-00006)",
    )
    rpt_p.add_argument(
        "--output", type=Path, default=None,
        help="出力ファイル。未指定時は標準出力 (CLI-00204)",
    )

    # ---- comparisons (CLI-00108) ---------------------------------------
    cmps_p = sub.add_parser(
        "comparisons",
        help="保存済み Comparison の一覧を表示する (CLI-00108)",
        description="Result Store の Comparison を JSON 配列で標準出力に列挙する。",
    )
    cmps_p.add_argument(
        "--store-root", required=True, type=Path,
        help="Result Store のルート",
    )
    cmps_p.add_argument(
        "--limit", type=int, default=None,
        help="表示件数の上限 (任意)",
    )

    # ---- list (CLI-00103) ----------------------------------------------
    list_p = sub.add_parser(
        "list",
        help="登録済み Task Profile / Model Candidate / Scorer を表示する (CLI-00103)",
        description=(
            "ユーザー設定ディレクトリから Task Profile / Model Candidate を"
            " 読み込み、組み込み Scorer 一覧と合わせて JSON で出力する"
            " (FUN-00104)。"
        ),
        epilog="例: local-llm-benchmark list --config-dir ./cfg --kind all",
    )
    list_p.add_argument(
        "--config-dir", required=True, type=Path,
        help="ユーザー設定ディレクトリ",
    )
    list_p.add_argument(
        "--kind",
        choices=("all", "task_profiles", "model_candidates", "scorers"),
        default="all",
        help="表示対象種別。既定は all",
    )

    # ---- runs (CLI-00104) ----------------------------------------------
    runs_p = sub.add_parser(
        "runs",
        help="保存済み Run の一覧を表示する (CLI-00104)",
        description="Result Store の Run を JSON 配列で標準出力に列挙する (FUN-00401)。",
    )
    runs_p.add_argument(
        "--store-root", required=True, type=Path,
        help="Result Store のルート",
    )
    runs_p.add_argument(
        "--limit", type=int, default=None,
        help="表示件数の上限 (任意)",
    )

    # ---- check (CLI-00105) ---------------------------------------------
    chk_p = sub.add_parser(
        "check",
        help="設定の事前検証を行う (CLI-00105)",
        description=(
            "Configuration Loader と同じ検証を Run 開始前に独立実行する"
            " (FUN-00105 / FUN-00402)。検出問題は CFG- 系 ID を含む 1 行 1 件で"
            " 標準出力に表示し、件数を終了コード (CLI-00303) に反映する。"
        ),
    )
    chk_p.add_argument(
        "--config-dir", required=True, type=Path,
        help="ユーザー設定ディレクトリ",
    )
    chk_p.add_argument(
        "--store-root", type=Path, default=None,
        help="Result Store のルート (CFG-00505 書込確認・CFG-00506 Comparison 検証用)",
    )
    chk_p.add_argument(
        "--comparison-config", type=Path, default=None,
        help="Comparison 設定 TOML を併せて検証する (CFG-00506)",
    )
    return parser


# ---- 進捗通知 (CLI-00203) -------------------------------------------------


def _emit_progress(event) -> None:
    kind = event.get("type")
    if kind == "run_started":
        print(f"[run] 開始: run_id={event['run_id']}", file=sys.stderr, flush=True)
    elif kind == "trial_completed":
        status = (
            "OK" if event["failure_kind"] is None
            else f"FAIL({event['failure_kind']})"
        )
        print(
            f"[trial] {event['task_profile']}/{event['case']} "
            f"{event['trial']}/{event['n_trials']} {status}",
            file=sys.stderr,
            flush=True,
        )
    elif kind == "run_aborted":
        print(
            f"[run] 中断: run_id={event['run_id']} reason={event['reason']}",
            file=sys.stderr,
            flush=True,
        )
    elif kind == "run_completed":
        print(
            f"[run] 完了: run_id={event['run_id']} dir={event['run_dir']}",
            file=sys.stderr,
            flush=True,
        )


# ---- run -------------------------------------------------------------------


def _cmd_run(args: argparse.Namespace) -> int:
    try:
        bundle = load_config_bundle(args.config_dir)
        run_config = load_run_config(args.run_config)
    except ConfigurationError as exc:
        print(f"[error] 設定不整合: {exc}", file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR
    try:
        plan = assemble_run_plan(
            run_config=run_config,
            catalog=bundle.catalog,
            models=bundle.models,
            providers=bundle.providers,
        )
    except ConfigurationError as exc:
        print(f"[error] Run 計画組立失敗: {exc}", file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    store_root = (
        args.store_root or run_config.store_root or Path("results")
    )
    store = ResultStore(store_root)
    coordinator = RunCoordinator(store=store)
    try:
        result = coordinator.execute(
            plan=plan,
            on_event=_emit_progress,
            config_source_root=str(bundle.source_root),
        )
    except Exception as exc:
        print(f"[error] Run 実行中に致命的失敗: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR

    summary_payload = {
        "run_id": result.run_id,
        "run_dir": result.run_dir,
        "model": plan.model_candidate.name,
        "n_trials": plan.n_trials,
        "task_profiles": [tp.name for tp in plan.task_profiles],
        "summary": {
            "score_mean": result.summary.score_mean,
            "latency_mean": result.summary.latency_mean,
            "output_tokens_mean": result.summary.output_tokens_mean,
            "success_trials": result.summary.success_trials,
            "failure_trials": result.summary.failure_trials,
        },
        "aborted": result.aborted,
        "abort_reason": result.abort_reason,
    }
    json.dump(summary_payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")

    if result.aborted:
        return EXIT_RUNTIME_ERROR
    if result.summary.failure_trials > 0:
        return EXIT_PARTIAL_FAILURE
    return EXIT_SUCCESS


# ---- compare ---------------------------------------------------------------


def _cmd_compare(args: argparse.Namespace) -> int:
    """`compare` サブコマンド (CLI-00107).

    入力 Run 識別子と重みは「CLI 引数 > Comparison 設定 > 既定値」の
    優先順で決定する (FUN-00310: 上書き値は Comparison メタに記録される)。
    """
    cfg = None
    if args.comparison_config is not None:
        try:
            cfg = load_comparison_config(args.comparison_config)
        except ConfigurationError as exc:
            print(f"[error] Comparison 設定不整合: {exc}", file=sys.stderr)
            return EXIT_CONFIGURATION_ERROR

    cli_runs = list(args.run_id)
    run_ids: list[str] = cli_runs or (list(cfg.run_ids) if cfg else [])
    if not run_ids:
        print(
            "[error] --run-id を 2 回以上指定するか --comparison-config を渡してください"
            " (DAT-00108)",
            file=sys.stderr,
        )
        return EXIT_USER_INPUT_ERROR

    axis = args.axis or (cfg.ranking_axis_default if cfg else "integrated")
    w_quality = (
        args.w_quality
        if args.w_quality is not None
        else (cfg.w_quality if cfg else 0.7)
    )
    w_speed = (
        args.w_speed if args.w_speed is not None
        else (cfg.w_speed if cfg else 0.3)
    )
    weights = ComparisonWeights(w_quality=w_quality, w_speed=w_speed)

    store = ResultStore(args.store_root)
    comparator = RunComparator(store=store)
    try:
        comparison = comparator.build(
            run_ids=run_ids,
            weights=weights,
            ranking_axis_default=axis,
        )
    except ComparisonError as exc:
        # DAT-00108 / DAT-00109 違反は user-input error として扱う (CLI-00302)
        print(f"[error] Comparison 生成失敗: {exc}", file=sys.stderr)
        return EXIT_USER_INPUT_ERROR
    except Exception as exc:
        print(f"[error] Comparison 実行中に致命的失敗: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR

    cmp_dir = store.write_comparison(comparison)
    print(
        f"[compare] 完了: comparison_id={comparison.comparison_id}"
        f" dir={cmp_dir}",
        file=sys.stderr,
        flush=True,
    )
    payload = {
        "comparison_id": comparison.comparison_id,
        "comparison_dir": str(cmp_dir),
        "run_ids": list(comparison.run_ids),
        "ranking_axis_default": comparison.ranking_axis_default,
        "weights": {
            "w_quality": weights.w_quality,
            "w_speed": weights.w_speed,
        },
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_SUCCESS


# ---- report ----------------------------------------------------------------


def _cmd_report(args: argparse.Namespace) -> int:
    """`report` サブコマンド (CLI-00102)."""
    store = ResultStore(args.store_root)
    try:
        if args.run_id:
            try:
                meta = store.load_meta(args.run_id)
                agg = store.load_aggregation(args.run_id)
            except FileNotFoundError as exc:
                print(f"[error] 該当なし: {exc}", file=sys.stderr)
                return EXIT_USER_INPUT_ERROR
            output = render_run_markdown(meta, agg)
        else:
            try:
                payload = store.load_comparison(args.comparison_id)
            except FileNotFoundError as exc:
                print(f"[error] 該当なし: {exc}", file=sys.stderr)
                return EXIT_USER_INPUT_ERROR
            output = render_comparison_markdown(payload)
    except Exception as exc:
        print(f"[error] レンダリング失敗: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"[report] 出力: {args.output}", file=sys.stderr, flush=True)
    else:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
    return EXIT_SUCCESS


# ---- comparisons -----------------------------------------------------------


def _cmd_comparisons(args: argparse.Namespace) -> int:
    """`comparisons` サブコマンド (CLI-00108)."""
    store = ResultStore(args.store_root)
    ids = store.list_comparisons()
    if args.limit is not None and args.limit >= 0:
        ids = ids[: args.limit]
    rows: list[dict] = []
    for cid in ids:
        try:
            payload = store.load_comparison(cid)
        except Exception:
            rows.append({"comparison_id": cid, "broken": True})
            continue
        rows.append(
            {
                "comparison_id": cid,
                "created_at": payload.get("created_at"),
                "run_ids": payload.get("run_ids") or [],
            }
        )
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_SUCCESS


# ---- list (CLI-00103) ------------------------------------------------------


def _cmd_list(args: argparse.Namespace) -> int:
    """`list` サブコマンド (CLI-00103, FUN-00104).

    Task Profile / Model Candidate / Scorer を JSON で標準出力に列挙する。
    出力構造はスクリプトから扱える形に揃える (CLI-00201)。
    """
    try:
        bundle = load_config_bundle(args.config_dir)
    except ConfigurationError as exc:
        # `check` と同じ表現に揃える (CLI-00103 失敗表示の規約)
        print(f"[error] 設定不整合: {exc}", file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    payload: dict[str, object] = {}
    if args.kind in ("all", "task_profiles"):
        payload["task_profiles"] = [
            {
                "name": tp.name,
                "purpose": tp.purpose,
                "description": tp.description,
                "scorer": tp.scorer.name,
                "cases": [c.name for c in tp.cases],
                "case_count": len(tp.cases),
            }
            for tp in bundle.catalog.profiles.values()
        ]
    if args.kind in ("all", "model_candidates"):
        payload["model_candidates"] = [
            {
                "name": mc.name,
                "label": mc.label,
                "provider_kind": mc.provider_kind,
                "provider_model_ref": mc.provider_model_ref,
            }
            for mc in bundle.models.values()
        ]
    if args.kind in ("all", "scorers"):
        payload["scorers"] = known_scorer_names()

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_SUCCESS


# ---- runs (CLI-00104) ------------------------------------------------------


def _cmd_runs(args: argparse.Namespace) -> int:
    """`runs` サブコマンド (CLI-00104, FUN-00401)."""
    store = ResultStore(args.store_root)
    ids = store.list_runs()
    if args.limit is not None and args.limit >= 0:
        ids = ids[: args.limit]
    rows: list[dict] = []
    for rid in ids:
        try:
            meta = store.load_meta(rid)
        except Exception:
            rows.append({"run_id": rid, "broken": True})
            continue
        mc = meta.get("model_candidate") or {}
        rows.append(
            {
                "run_id": rid,
                "started_at": meta.get("started_at"),
                "model": mc.get("name"),
                "task_profiles": meta.get("task_profiles") or [],
                "n_trials": meta.get("n_trials"),
            }
        )
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return EXIT_SUCCESS


# ---- check (CLI-00105) -----------------------------------------------------


def _cmd_check(args: argparse.Namespace) -> int:
    """`check` サブコマンド (CLI-00105, FUN-00105 / FUN-00402).

    検出した問題は標準出力に 1 行 1 件で表示し、件数を終了コードに
    反映する (問題ありなら CLI-00303)。読込自体に失敗した場合も同じ
    表現に揃える (CLI-00103/00105 共通)。
    """
    # 問題件数のカウンター。設定読込失敗・Comparison 検証時の追加エラーも
    # ここに集約する。
    extra_count = 0
    try:
        bundle = load_config_bundle(args.config_dir)
    except ConfigurationError as exc:
        print(f"[check] CFG-LOAD: {exc}")
        print("問題件数: 1", file=sys.stderr)
        return EXIT_CONFIGURATION_ERROR

    issues = check_bundle(bundle, store_root=args.store_root)
    for it in issues:
        print(f"[check] {it.code} ({it.where}): {it.message}")

    # CFG-00506 (Comparison)
    if args.comparison_config is not None:
        if args.store_root is None:
            print(
                "[check] CFG-00506 (comparison):"
                " --store-root の指定が必要"
            )
            extra_count += 1
        else:
            try:
                cmp_cfg = load_comparison_config(args.comparison_config)
            except ConfigurationError as exc:
                print(f"[check] CFG-00207 (comparison): {exc}")
                extra_count += 1
            else:
                cmp_issues = check_comparison(cmp_cfg, args.store_root)
                for it in cmp_issues:
                    print(f"[check] {it.code} ({it.where}): {it.message}")
                issues.extend(cmp_issues)

    total = len(issues) + extra_count
    if total == 0:
        print("問題なし")
        return EXIT_SUCCESS

    print(f"問題件数: {total}", file=sys.stderr)
    return EXIT_CONFIGURATION_ERROR


# ---- ディスパッチ ---------------------------------------------------------


_DISPATCH = {
    "run": _cmd_run,
    "compare": _cmd_compare,
    "report": _cmd_report,
    "comparisons": _cmd_comparisons,
    "list": _cmd_list,
    "runs": _cmd_runs,
    "check": _cmd_check,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    # CLI-00302: argparse 自身が出すユーザー入力誤り (未知サブコマンド・必須
    # 引数欠落・型変換失敗等) を SystemExit(2) として送出する仕様を尊重し、
    # ここでは捕捉して終了コード EXIT_USER_INPUT_ERROR に正規化する。
    # `--help`/`--version` は SystemExit(0) を投げるため、その場合は通す。
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code in (0, None):
            return EXIT_SUCCESS
        return EXIT_USER_INPUT_ERROR

    handler = _DISPATCH.get(args.command)
    if handler is None:  # pragma: no cover - argparse が required で防ぐ
        parser.error(f"未知のサブコマンド: {args.command}")
        return EXIT_USER_INPUT_ERROR
    return handler(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
