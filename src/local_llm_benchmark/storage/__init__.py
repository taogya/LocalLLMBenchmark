"""Result Store (TASK-00007-01 / TASK-00007-02, COMP-00009).

Run / Comparison 結果を識別子単位のディレクトリに保存する.

設計依拠:
- ARCH-00204 1 Run = 1 ディレクトリ。原子的に完成させる
- NFR-00103 生応答と正規化済み集計値を分離保存する
- DAT-00201 結果スキーマには版を埋め込む (SCHEMA_VERSION)
- COMP-00009 Comparison も Comparison 識別子単位で保存し、Run 識別子集合
  とランキング軸設定を含める

ファイル構成 (本実装で確定):
    <store_root>/<run_id>/
        meta.json           # Run メタ + provider 識別 + 生成条件
        aggregation.json    # CaseAggregation 群 + RunSummary
        raw/trials.jsonl    # 生応答を含む全 Trial 詳細
    <store_root>/comparisons/<comparison_id>/
        comparison.json     # Comparison 入力 (run_ids, weights, axis) +
                            # ComparisonReport (per-model + 3 軸ランキング)

原子性は「全部 tmp ディレクトリに書き出してから rename」で確保する。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .. import SCHEMA_VERSION
from ..models import CaseAggregation, Comparison, RunSummary, Trial


# Comparison 配下の固定サブディレクトリ名 (Run 識別子と物理的に衝突させない)
COMPARISONS_DIRNAME = "comparisons"


def _to_jsonable(obj: Any) -> Any:
    """dataclass / Mapping / Sequence を素直な JSON 型に落とす."""
    if is_dataclass(obj):
        return {k: _to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Mapping):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    return obj


def generate_run_id(model_name: str, now: datetime | None = None) -> str:
    """Run 識別子を生成する.

    形式: `run-YYYYMMDD-HHMMSS-<modelslug>`
    """
    ts = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    slug = "".join(
        ch if ch.isalnum() or ch in "-_." else "_" for ch in model_name
    )
    return f"run-{ts}-{slug}"


def generate_comparison_id(
    run_ids: Sequence[str], now: datetime | None = None
) -> str:
    """Comparison 識別子を生成する (TASK-00007-02).

    形式: `cmp-YYYYMMDD-HHMMSS-n<件数>` (Run 数の概算を末尾に添える)。
    Run 識別子そのものを連結すると長くなりすぎるため件数のみとする。
    """
    ts = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return f"cmp-{ts}-n{len(run_ids)}"


class ResultStore:
    """Run 永続化."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def write_run(
        self,
        run_id: str,
        meta: Mapping[str, Any],
        trials: Sequence[Trial],
        aggregations: Sequence[CaseAggregation],
        run_summary: RunSummary,
    ) -> Path:
        """Run 結果を原子的に書き出す.

        ARCH-00204: 進行中ディレクトリを `<run_id>.partial` に作り、完了
        時に `<run_id>` へ rename する。これによりクラッシュ時に
        中途半端なディレクトリを完成扱いしない。
        """
        self.root.mkdir(parents=True, exist_ok=True)
        partial = self.root / f"{run_id}.partial"
        final = self._run_dir(run_id)
        if partial.exists():
            # 残留があれば消す (前回失敗の可能性)
            _rmtree(partial)
        partial.mkdir(parents=True)
        raw_dir = partial / "raw"
        raw_dir.mkdir()

        meta_payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            **_to_jsonable(meta),
        }
        _write_json(partial / "meta.json", meta_payload)
        _write_json(
            partial / "aggregation.json",
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "case_aggregations": [_to_jsonable(a) for a in aggregations],
                "run_summary": _to_jsonable(run_summary),
            },
        )
        _write_jsonl(
            raw_dir / "trials.jsonl",
            (_to_jsonable(t) for t in trials),
        )

        if final.exists():
            _rmtree(final)
        os.rename(partial, final)
        return final

    def list_runs(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            p.name
            for p in self.root.iterdir()
            if p.is_dir()
            and not p.name.endswith(".partial")
            and p.name != COMPARISONS_DIRNAME
        )

    def load_meta(self, run_id: str) -> Mapping[str, Any]:
        path = self._run_dir(run_id) / "meta.json"
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load_aggregation(self, run_id: str) -> Mapping[str, Any]:
        """Run の集計値を読む (TASK-00007-02).

        Run Comparator (COMP-00011) が CaseAggregation 群と RunSummary を
        読み出すための入口。生応答 (raw/) には触らない (NFR-00103)。
        """
        path = self._run_dir(run_id) / "aggregation.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"Run の集計値が見つからない: run_id={run_id}"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # ---- Comparison 永続化 (TASK-00007-02) -------------------------------

    def _comparisons_root(self) -> Path:
        return self.root / COMPARISONS_DIRNAME

    def _comparison_dir(self, comparison_id: str) -> Path:
        return self._comparisons_root() / comparison_id

    def write_comparison(self, comparison: Comparison) -> Path:
        """Comparison を原子的に書き出す (COMP-00009 / DAT-00009).

        Run と同様に `.partial` で書いて rename する。
        """
        root = self._comparisons_root()
        root.mkdir(parents=True, exist_ok=True)
        partial = root / f"{comparison.comparison_id}.partial"
        final = self._comparison_dir(comparison.comparison_id)
        if partial.exists():
            _rmtree(partial)
        partial.mkdir(parents=True)

        payload = {
            "schema_version": SCHEMA_VERSION,
            "comparison_id": comparison.comparison_id,
            "created_at": comparison.created_at,
            "run_ids": list(comparison.run_ids),
            "ranking_axis_default": comparison.ranking_axis_default,
            "weights": _to_jsonable(comparison.weights),
            "report": _to_jsonable(comparison.report),
        }
        _write_json(partial / "comparison.json", payload)

        if final.exists():
            _rmtree(final)
        os.rename(partial, final)
        return final

    def list_comparisons(self) -> list[str]:
        root = self._comparisons_root()
        if not root.is_dir():
            return []
        return sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and not p.name.endswith(".partial")
        )

    def load_comparison(self, comparison_id: str) -> Mapping[str, Any]:
        path = self._comparison_dir(comparison_id) / "comparison.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"Comparison が見つからない: {comparison_id}"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


# ---- 内部ヘルパー ---------------------------------------------------------


def _write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _write_jsonl(path: Path, rows) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False))
            f.write("\n")
    os.replace(tmp, path)


def _rmtree(path: Path) -> None:
    # shutil.rmtree を避け、標準ライブラリで簡素に消す
    if not path.exists():
        return
    if path.is_file() or path.is_symlink():
        path.unlink()
        return
    for child in path.iterdir():
        _rmtree(child)
    path.rmdir()
