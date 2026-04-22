#!/usr/bin/env python3
"""
TASK-00004-03: progress task ファイルのフォーマット検査。

- 必須フィールド: `Status:`, `Role:`, `Related IDs:`
- 子 task のみ `Parent:` を必須とする (ファイル名 TASK-NNNNN-SS-*.md)
- Status 値: open|in-progress|review-pending|done|cancelled
- Role 値: project-master|solution-architect|programmer|reviewer|docs-writer
- ファイル名: 親 `TASK-NNNNN-*.md`, 子 `TASK-NNNNN-SS-*.md`
- 除外: progress/_templates/, progress/README.md, .gitkeep, v0.1.0/
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


VALID_STATUS = {"open", "in-progress", "review-pending", "done", "cancelled"}
VALID_ROLE = {"project-master", "solution-architect", "programmer", "reviewer", "docs-writer"}

PARENT_NAME_RE = re.compile(r"^TASK-\d{5}-[a-z0-9-]+\.md$")
CHILD_NAME_RE = re.compile(r"^TASK-\d{5}-\d{2}-[a-z0-9-]+\.md$")


def field(lines: list[str], name: str) -> tuple[int, str] | None:
    """`- <name>: <value>` 形式のフィールドを返す。"""
    pat = re.compile(rf"^\s*-\s*{re.escape(name)}\s*:\s*(.*)$")
    for i, line in enumerate(lines, start=1):
        m = pat.match(line)
        if m:
            return i, m.group(1).strip()
    return None


def check():
    findings: list[Finding] = []
    for path in iter_files(extensions=[".md"], include_dirs=["progress"], include_files=[]):
        rel = path.relative_to(REPO_ROOT).as_posix()
        # 除外
        if rel.startswith("progress/_templates/"):
            continue
        if rel == "progress/README.md":
            continue
        name = path.name

        is_child = bool(CHILD_NAME_RE.match(name))
        is_parent = bool(PARENT_NAME_RE.match(name)) and not is_child
        if not (is_child or is_parent):
            findings.append(
                Finding(path, 1, f"ファイル名が TASK-NNNNN[-SS]-<slug>.md 形式ではない: {name}")
            )
            continue

        lines = read_lines(path)

        # Status
        s = field(lines, "Status")
        if s is None:
            findings.append(Finding(path, 1, "必須フィールド `Status:` が無い"))
        else:
            line_no, val = s
            if val not in VALID_STATUS:
                findings.append(
                    Finding(path, line_no, f"Status 値が不正: '{val}' (許容: {sorted(VALID_STATUS)})")
                )

        # Role
        r = field(lines, "Role")
        if r is None:
            findings.append(Finding(path, 1, "必須フィールド `Role:` が無い"))
        else:
            line_no, val = r
            if val not in VALID_ROLE:
                findings.append(
                    Finding(path, line_no, f"Role 値が不正: '{val}' (許容: {sorted(VALID_ROLE)})")
                )

        # Related IDs
        if field(lines, "Related IDs") is None:
            findings.append(Finding(path, 1, "必須フィールド `Related IDs:` が無い"))

        # Parent (子 task のみ必須)
        if is_child:
            p = field(lines, "Parent")
            if p is None:
                findings.append(Finding(path, 1, "子 task は `Parent:` 必須"))
            else:
                line_no, val = p
                if not re.match(r"^TASK-\d{5}$", val):
                    findings.append(
                        Finding(path, line_no, f"Parent 形式が不正: '{val}' (期待: TASK-NNNNN)")
                    )
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
