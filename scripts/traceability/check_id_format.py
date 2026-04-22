#!/usr/bin/env python3
"""
TASK-00004-03: ID フォーマット検査。

全 ID が `<Prefix>-NNNNN` (5 桁 0 埋め) を満たすかを検査する。
既知 prefix (REQ, FUN, ... ) が登場し、かつ桁数が違う、もしくは小文字
混じりの場合は違反として報告する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    KNOWN_PREFIXES,
    iter_files,
    main_wrapper,
    read_lines,
)


# 大小混合 / 桁不足 / 桁過多を検出する loose パターン
LOOSE = re.compile(r"\b([A-Za-z]+)-(\d+)\b")
STRICT = re.compile(r"\b[A-Z]+-\d{5}\b")
# 既知 prefix の小文字版
KNOWN_PREFIXES_LOWER = {p.lower() for p in KNOWN_PREFIXES}


def check():
    findings: list[Finding] = []
    md_files = list(iter_files(extensions=[".md"]))
    for path in md_files:
        for i, line in enumerate(read_lines(path), start=1):
            for m in LOOSE.finditer(line):
                prefix = m.group(1)
                digits = m.group(2)
                # ID 候補と判断する条件: prefix が KNOWN (大小無視)
                if prefix.upper() not in KNOWN_PREFIXES:
                    continue
                # 厳密一致なら問題なし
                if prefix in KNOWN_PREFIXES and len(digits) == 5:
                    continue
                # 小文字混じり / 桁数違い → 違反
                reason = (
                    f"ID フォーマット違反: '{m.group(0)}' "
                    f"(期待: 大文字prefix + '-' + 5桁0埋め)"
                )
                findings.append(Finding(path, i, reason))
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
