"""task_id 00001-03, 00004-02, 00007-02, 00011-02, 00015-02:
設定駆動 benchmark CLI。
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import TextIO

from local_llm_benchmark.benchmark.runner import BenchmarkRunner
from local_llm_benchmark.cli.report import (
    render_comparison_report,
    render_run_report,
)
from local_llm_benchmark.cli.suite_catalog import (
    render_suite_detail,
    render_suite_list,
)
from local_llm_benchmark.config.loader import (
    build_benchmark_plan,
    load_config_bundle,
)
from local_llm_benchmark.prompts.repository import InMemoryPromptRepository
from local_llm_benchmark.providers.base import ProviderError
from local_llm_benchmark.providers.factory import build_provider_adapters
from local_llm_benchmark.registry.model_registry import InMemoryModelRegistry
from local_llm_benchmark.storage.jsonl import JsonlResultSink


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="local-llm-benchmark",
        description="外部設定でローカル LLM ベンチマークを実行する CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="外部設定から benchmark suite を実行する",
    )
    run_parser.add_argument(
        "--config-root",
        required=True,
        help=(
            "benchmark_suites などの設定を読むルート。prompts は同階層、"
            "または sibling の prompts から解決する"
        ),
    )
    run_parser.add_argument(
        "--suite",
        required=True,
        help="実行する benchmark suite の ID",
    )
    run_parser.add_argument(
        "--run-id",
        help="省略時は suite ID と時刻から自動生成する",
    )
    run_parser.add_argument(
        "--output-dir",
        default="tmp/results",
        help="結果保存先のルート。run_id ごとのサブディレクトリは自動作成する",
    )
    run_parser.set_defaults(handler=_handle_run)

    suites_parser = subparsers.add_parser(
        "suites",
        help="利用可能な benchmark suite と準備対象を表示する",
    )
    suites_parser.add_argument(
        "suite_id",
        nargs="?",
        help="指定すると benchmark suite の詳細を表示する",
    )
    suites_parser.add_argument(
        "--config-root",
        required=True,
        help=(
            "benchmark_suites などの設定を読むルート。prompts は同階層、"
            "または sibling の prompts から解決する"
        ),
    )
    suites_parser.set_defaults(handler=_handle_suites)

    report_parser = subparsers.add_parser(
        "report",
        help="保存済み run の metric 要約を表示する",
        description="保存済み run の metric 要約を表示する",
    )
    report_parser.add_argument(
        "--run-dir",
        required=True,
        help="manifest.json と run-metrics.json を読む run directory",
    )
    report_parser.set_defaults(handler=_handle_report)

    compare_parser = subparsers.add_parser(
        "compare",
        help="保存済み run の metric 差分を表示する",
        description="保存済み run の metric 差分を表示する",
    )
    compare_parser.add_argument(
        "--run-dir",
        action="append",
        required=True,
        help=(
            "比較対象の run directory。2 回以上指定し、先頭を baseline "
            "として扱う"
        ),
    )
    compare_parser.set_defaults(handler=_handle_compare)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    try:
        return int(args.handler(args, output, errors))
    except (ProviderError, ValueError, KeyError, FileNotFoundError) as exc:
        print(f"エラー: {exc}", file=errors)
        return 1


def _handle_run(
    args: argparse.Namespace,
    stdout: TextIO,
    _stderr: TextIO,
) -> int:
    bundle = load_config_bundle(args.config_root)
    plan = build_benchmark_plan(
        bundle,
        suite_id=args.suite,
        run_id=args.run_id,
        trace_metadata={"config_root": args.config_root},
    )
    result_sink = JsonlResultSink(Path(args.output_dir), plan)
    runner = BenchmarkRunner(
        model_registry=InMemoryModelRegistry(list(bundle.model_specs)),
        prompt_repository=InMemoryPromptRepository(
            list(bundle.prompt_specs),
            list(bundle.prompt_sets),
        ),
        provider_adapters=build_provider_adapters(
            bundle.app_config.provider_profiles
        ),
        result_sink=result_sink,
    )
    try:
        records = runner.run(plan)
    finally:
        result_sink.close()

    _print_summary(
        plan.run_id,
        plan.suite_id,
        records,
        result_sink.run_dir,
        stdout,
    )
    return 0 if all(record.error is None for record in records) else 1


def _handle_suites(
    args: argparse.Namespace,
    stdout: TextIO,
    _stderr: TextIO,
) -> int:
    bundle = load_config_bundle(args.config_root)
    if args.suite_id:
        print(
            render_suite_detail(
                bundle,
                args.suite_id,
                config_root=args.config_root,
            ),
            file=stdout,
        )
        return 0

    print(
        render_suite_list(bundle, config_root=args.config_root),
        file=stdout,
    )
    return 0


def _handle_report(
    args: argparse.Namespace,
    stdout: TextIO,
    _stderr: TextIO,
) -> int:
    print(render_run_report(Path(args.run_dir)), file=stdout)
    return 0


def _handle_compare(
    args: argparse.Namespace,
    stdout: TextIO,
    _stderr: TextIO,
) -> int:
    print(render_comparison_report(args.run_dir), file=stdout)
    return 0


def _print_summary(
    run_id: str,
    suite_id: str,
    records: list,
    result_dir: Path,
    stdout: TextIO,
) -> None:
    success_count = sum(1 for record in records if record.error is None)
    error_count = len(records) - success_count
    print(f"run_id: {run_id}", file=stdout)
    print(f"suite_id: {suite_id}", file=stdout)
    print(f"result_dir: {result_dir}", file=stdout)
    print(f"records: {len(records)}", file=stdout)
    print(f"success: {success_count}", file=stdout)
    print(f"errors: {error_count}", file=stdout)
    for record in records:
        status = "error" if record.error else "ok"
        detail = record.error
        if detail is None and record.response is not None:
            detail = record.response.output_text
        compact_detail = _compact_text(detail or "")
        print(
            f"- {record.model_key} | {record.prompt_id} | "
            f"{status} | {compact_detail}",
            file=stdout,
        )


def _compact_text(text: str, max_length: int = 160) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."
