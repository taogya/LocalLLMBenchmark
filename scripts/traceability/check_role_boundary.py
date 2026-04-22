#!/usr/bin/env python3
"""
TASK-00004-03: ロール境界検査。

`progress/<role>/TASK-*.md` の `Role:` 値とディレクトリが一致するかを検査する。
- `progress/_templates/` と `progress/README.md` は除外
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


VALID_ROLES = {"project-master", "solution-architect", "programmer", "reviewer", "docs-writer"}
ROLE_FIELD_RE = re.compile(r"^\s*-\s*Role\s*:\s*(.*)$")


def check():
    findings: list[Finding] = []
    for path in iter_files(extensions=[".md"], include_dirs=["progress"], include_files=[]):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith("progress/_templates/"):
            continue
        if rel == "progress/README.md":
            continue
        if not path.name.startswith("TASK-"):
            continue
        # ディレクトリ名取得
        try:
            dir_role = path.relative_to(REPO_ROOT / "progress").parts[0]
        except (IndexError, ValueError):
            continue
        if dir_role not in VALID_ROLES:
            findings.append(Finding(path, 1, f"配置ディレクトリが未知のロール: {dir_role}"))
            continue
        lines = read_lines(path)
        for i, line in enumerate(lines, start=1):
            m = ROLE_FIELD_RE.match(line)
            if m:
                val = m.group(1).strip()
                if val != dir_role:
                    findings.append(
                        Finding(path, i, f"Role フィールド '{val}' とディレクトリ '{dir_role}' が不一致")
                    )
                break
        else:
            findings.append(Finding(path, 1, "`Role:` フィールドが見つからない"))
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
