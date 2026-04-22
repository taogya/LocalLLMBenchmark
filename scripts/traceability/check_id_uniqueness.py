#!/usr/bin/env python3
"""
TASK-00004-03: ID 一意性 / 欠番検査。

- 同一カテゴリ内で「定義」が重複していないか
  - 定義 = テーブル行の先頭セル, または見出し行に出現する ID
  - supersede された ID も「定義済み」として扱う
- 同一カテゴリの「百の位 (subgroup)」内で番号が連続しているか
  - 例: FUN-00101..00105 / FUN-00201..00207 / FUN-00301..00309
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    REPO_ROOT,
    collect_definitions,
    iter_files,
    main_wrapper,
)


# 定義の元となるドキュメントは docs/ 配下と progress/ (TASK 用)
DEF_DIRS = ["docs"]


def check():
    findings: list[Finding] = []
    paths = list(iter_files(extensions=[".md"], include_dirs=DEF_DIRS, include_files=[]))
    defs = collect_definitions(paths)

    # 重複検出: 同一ファイル内の複数定義 (表 + 見出し) は許容し、
    # ファイル間重複のみをエラーとする。
    for tid, occurrences in sorted(defs.items()):
        files = list({occ.file for occ in occurrences})
        if len(files) <= 1:
            continue
        for occ in occurrences[1:]:
            if occ.file == occurrences[0].file:
                continue
            findings.append(
                Finding(
                    occ.file,
                    occ.line,
                    f"ID '{tid}' が複数ファイルで定義されています "
                    f"(初出: {occurrences[0].file.relative_to(REPO_ROOT)}:{occurrences[0].line})",
                )
            )

    # 欠番検出 (subgroup = number // 100)
    by_prefix_bucket: dict[tuple[str, int], set[int]] = defaultdict(set)
    bucket_first_occ: dict[tuple[str, int, int], Finding] = {}
    for tid, occurrences in defs.items():
        prefix, num_str = tid.split("-")
        n = int(num_str)
        bucket = n // 100
        by_prefix_bucket[(prefix, bucket)].add(n)
        bucket_first_occ[(prefix, bucket, n)] = occurrences[0]

    for (prefix, bucket), nums in sorted(by_prefix_bucket.items()):
        sorted_nums = sorted(nums)
        lo, hi = sorted_nums[0], sorted_nums[-1]
        present = set(sorted_nums)
        missing = [n for n in range(lo, hi + 1) if n not in present]
        if not missing:
            continue
        # 欠番情報を最も近い既存定義の位置に紐付ける
        any_occ = bucket_first_occ[(prefix, bucket, sorted_nums[0])]
        missing_ids = ", ".join(f"{prefix}-{n:05d}" for n in missing)
        findings.append(
            Finding(
                any_occ.file,
                any_occ.line,
                f"カテゴリ {prefix} の subgroup {bucket}xx に欠番: {missing_ids}",
            )
        )

    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
