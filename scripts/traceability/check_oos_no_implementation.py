#!/usr/bin/env python3
"""
TASK-00004-03: OOS- 実装混入検査。

(1) `src/`, `tests/`, `configs/`, `prompts/` 内に `OOS-NNNNN` が出現していないか
(2) `progress/**/*.md` のうち Status が `cancelled` または `done` 以外の active task の
    `Related IDs:` 行に `OOS-NNNNN` が出現していないか
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    REPO_ROOT,
    iter_files,
    main_wrapper,
    read_lines,
)


OOS_RE = re.compile(r"\bOOS-\d{5}\b")
STATUS_RE = re.compile(r"^\s*-\s*Status\s*:\s*(.*)$")
RELATED_RE = re.compile(r"^\s*-\s*Related IDs\s*:\s*(.*)$")


def check():
    findings: list[Finding] = []

    # (1) src/tests/configs/prompts 配下
    for path in iter_files(
        extensions=None,
        include_dirs=["src", "tests", "configs", "prompts"],
        include_files=[],
    ):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if OOS_RE.search(line):
                findings.append(Finding(path, i, "実装系ディレクトリに OOS- が出現"))

    # (2) active progress task の Related IDs:
    for path in iter_files(extensions=[".md"], include_dirs=["progress"], include_files=[]):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith("progress/_templates/") or rel == "progress/README.md":
            continue
        if not path.name.startswith("TASK-"):
            continue
        lines = read_lines(path)
        status = None
        for line in lines:
            m = STATUS_RE.match(line)
            if m:
                status = m.group(1).strip()
                break
        if status in {"done", "cancelled"}:
            continue
        for i, line in enumerate(lines, start=1):
            m = RELATED_RE.match(line)
            if m and OOS_RE.search(m.group(1)):
                findings.append(
                    Finding(path, i, f"active task ({status}) の Related IDs に OOS- が含まれる")
                )
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
