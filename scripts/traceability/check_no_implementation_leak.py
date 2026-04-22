#!/usr/bin/env python3
"""
TASK-00004-03: 設計文書への実装具体の混入検査。

対象: `docs/requirements/`, `docs/design/`
- 検出語句: argparse, click, httpx, requests, pydantic, dataclass, asyncio, @property,
  および Python の構文片 (`def \\w+\\(`, `class \\w+\\(`, `import \\w+`, `from \\w+ import`)
- 検出対象は「コードフェンス内」または「インラインコード内」に限る
  - 散文中のメタ言及 (例: 「argparse / click 等」) は許容
- 例外: `_common.py` の IMPL_LEAK_WHITELIST_TERMS
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    IMPL_LEAK_WHITELIST_TERMS,
    in_fenced_code_blocks,
    iter_files,
    main_wrapper,
    read_lines,
)


LIB_TERMS = [
    "argparse", "click", "httpx", "requests", "pydantic", "dataclasses", "dataclass",
    "asyncio", "@property", "fastapi", "flask", "django", "sqlalchemy",
]
CODE_PATTERNS = [
    re.compile(r"\bdef\s+\w+\s*\("),
    re.compile(r"\bclass\s+\w+\s*\("),
    re.compile(r"\bimport\s+\w+"),
    re.compile(r"\bfrom\s+\w+\s+import\b"),
]
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def check():
    findings: list[Finding] = []
    target_dirs = ["docs/requirements", "docs/design"]
    for path in iter_files(extensions=[".md"], include_dirs=target_dirs, include_files=[]):
        lines = read_lines(path)
        in_block = in_fenced_code_blocks(lines)
        for i, line in enumerate(lines, start=1):
            inside_fence = in_block[i - 1]
            # フェンス内の場合: 行全体を検査対象
            if inside_fence:
                snippets = [line]
            else:
                # 散文行: インラインコードのみ検査対象
                snippets = INLINE_CODE_RE.findall(line)
            for snippet in snippets:
                for term in LIB_TERMS:
                    if term in IMPL_LEAK_WHITELIST_TERMS:
                        continue
                    # 単語境界
                    if term.startswith("@"):
                        if term in snippet:
                            findings.append(
                                Finding(path, i, f"設計文書に実装具体が混入: '{term}'")
                            )
                    else:
                        if re.search(rf"\b{re.escape(term)}\b", snippet):
                            findings.append(
                                Finding(path, i, f"設計文書に実装具体が混入: '{term}'")
                            )
                for pat in CODE_PATTERNS:
                    if pat.search(snippet):
                        findings.append(
                            Finding(path, i, f"設計文書に Python コード片が混入: '{pat.pattern}'")
                        )
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
