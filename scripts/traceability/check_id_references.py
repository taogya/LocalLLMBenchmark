#!/usr/bin/env python3
"""
TASK-00004-03: ID 参照の整合性検査。

文書内で参照される ID が定義済みかを検査する。

- 定義済み = `docs/requirements/`, `docs/design/`, `docs/development/` 配下に
  出現する ID 全て (テーブル / 見出し / 本文すべての出現を含む)
- TASK- ID は `progress/` 配下のファイル名と本文出現を定義として扱う
- 走査対象 = 全 markdown (docs / progress / .github / README)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    ID_PATTERN,
    KNOWN_PREFIXES,
    REPO_ROOT,
    iter_files,
    main_wrapper,
    read_lines,
)


DEF_DOC_DIRS = ["docs/requirements", "docs/design", "docs/development"]
TASK_FILENAME_RE = re.compile(r"^(TASK-\d{5})(?:-\d{2})?-")


def collect_defined_ids() -> set[str]:
    defined: set[str] = set()
    # docs 配下に出現するすべての ID を定義として扱う
    for path in iter_files(extensions=[".md"], include_dirs=DEF_DOC_DIRS, include_files=[]):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for prefix, num in ID_PATTERN.findall(text):
            if prefix not in KNOWN_PREFIXES:
                continue
            defined.add(f"{prefix}-{num}")

    # progress 配下のファイル名と本文に登場する TASK- を定義として扱う
    for path in iter_files(extensions=[".md"], include_dirs=["progress"], include_files=[]):
        m = TASK_FILENAME_RE.match(path.name)
        if m:
            defined.add(m.group(1))
        text = path.read_text(encoding="utf-8", errors="ignore")
        for prefix, num in ID_PATTERN.findall(text):
            if prefix == "TASK":
                defined.add(f"{prefix}-{num}")
    return defined


def check():
    defined = collect_defined_ids()
    findings: list[Finding] = []

    target_dirs = ["docs", "progress", ".github", "scripts"]
    for path in iter_files(extensions=[".md"], include_dirs=target_dirs, include_files=["README.md"]):
        for i, line in enumerate(read_lines(path), start=1):
            for prefix, num in ID_PATTERN.findall(line):
                if prefix not in KNOWN_PREFIXES:
                    continue
                tid = f"{prefix}-{num}"
                if tid not in defined:
                    findings.append(
                        Finding(path, i, f"未定義 ID への参照: {tid}")
                    )
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
