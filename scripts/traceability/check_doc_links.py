#!/usr/bin/env python3
"""
TASK-00004-03: ドキュメント内リンク / パス参照の存在検査。

- Markdown リンク `[text](path)` の path 部分の存在検証
- 本文中の path 文字列 (`.md|.py|.toml|.json|.yaml|.yml|.sh` 拡張子) の存在検証
- 外部 URL (http(s)://) は対象外
- `#anchor` 付きはパス部分のみ検査
- ワークスペースルート相対 / 当該ファイルからの相対の双方を許容
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


MD_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BARE_PATH_RE = re.compile(r"(?<![\w/])((?:[\w./-]+)\.(?:md|py|toml|json|yaml|yml|sh))(?![\w/])")
URL_PREFIXES = ("http://", "https://", "mailto:", "tel:")


def resolve_candidates(path_str: str, base: Path) -> list[Path]:
    """path_str を解決した候補リストを返す (順に exists() を試す)。"""
    p = path_str.split("#", 1)[0].split("?", 1)[0]
    if not p:
        return []
    if p.startswith(("/", "//")):
        # 絶対パス指定 → リポジトリルート相対として解釈
        return [REPO_ROOT / p.lstrip("/")]
    candidates: list[Path] = []
    # 1) ファイル相対 (Markdown 標準)
    candidates.append((base.parent / p))
    # 2) リポジトリルート相対 (本文中の bare path 等)
    candidates.append(REPO_ROOT / p)
    return candidates


def is_external(url: str) -> bool:
    return url.startswith(URL_PREFIXES)


def check():
    findings: list[Finding] = []
    md_files = list(iter_files(extensions=[".md"]))
    for path in md_files:
        lines = read_lines(path)
        in_fence = False
        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            # 1) Markdown リンク (インラインコード内は除外)
            link_targets: set[str] = set()
            line_no_inline_code = re.sub(r"`[^`]*`", " ", line)
            for m in MD_LINK_RE.finditer(line_no_inline_code):
                target = m.group(1).strip()
                link_targets.add(target.split("#", 1)[0])
                if not target or is_external(target) or target.startswith("#"):
                    continue
                # mailto: 等
                if ":" in target.split("/", 1)[0]:
                    continue
                cands = resolve_candidates(target, path)
                if cands and not any(c.exists() for c in cands):
                    rel_target = target.split("#", 1)[0]
                    findings.append(
                        Finding(path, i, f"リンク先が存在しない: {rel_target}")
                    )

            # 2) 裸のパス文字列 (リンク内・インラインコード除外)
            cleaned = re.sub(r"`[^`]*`", " ", line)
            cleaned = MD_LINK_RE.sub(" ", cleaned)
            for m in BARE_PATH_RE.finditer(cleaned):
                target = m.group(1).rstrip(".,;:")
                if target in link_targets:
                    continue
                # URL 内の一部を排除
                start = m.start()
                if start >= 1 and cleaned[start - 1] in "/=":
                    continue
                # "/" を含まない単独 file 名は誤検知抑止のため対象外
                if "/" not in target:
                    continue
                cands = resolve_candidates(target, path)
                if cands and not any(c.exists() for c in cands):
                    findings.append(
                        Finding(path, i, f"パスが存在しない: {target}")
                    )
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
