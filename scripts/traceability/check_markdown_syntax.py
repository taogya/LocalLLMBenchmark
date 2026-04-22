#!/usr/bin/env python3
"""
TASK-00004-03: Markdown 構文の軽量検査。

- コードフェンス (` ``` ` / `~~~`) の開閉バランス
- リンク `[text](url)` の括弧バランス (行単位)
- 表の列数整合 (区切り行 `|---|` と本体行の `|` 個数一致)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    iter_files,
    main_wrapper,
    read_lines,
)


SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


def check_fences(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    open_count = 0
    last_open_line = 0
    for i, line in enumerate(lines, start=1):
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            if open_count == 0:
                open_count = 1
                last_open_line = i
            else:
                open_count = 0
    if open_count != 0:
        findings.append(
            Finding(path, last_open_line, "コードフェンスの開閉が一致していない")
        )
    return findings


def check_link_brackets(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    in_fence = False
    for i, line in enumerate(lines, start=1):
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # インラインコードを除去
        cleaned = re.sub(r"`[^`]*`", "", line)
        # リンク文字列のみ抽出して検査するのは複雑。ここでは
        # `]( ` パターンが行内に出現したものについて、対応する括弧の整合のみ確認する。
        # 単純な `[a](b)` の整合性: 行内の `[`, `]`, `(`, `)` を素直に数える…はリスト記法と
        # 衝突するため、ここでは「`]( ` が出現した行」のみ括弧整合を強制する。
        for m in re.finditer(r"\]\(", cleaned):
            start = m.start()
            # `[` が直前のどこかに、対応する `]` が start にある
            # `(` が start+1 にあって、対応する `)` が後ろにあるか確認
            depth = 0
            close_idx = -1
            for j in range(start + 1, len(cleaned)):
                ch = cleaned[j]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        close_idx = j
                        break
            if close_idx == -1:
                findings.append(
                    Finding(path, i, "リンク `[..](..)` の括弧が閉じていない")
                )
    return findings


def check_tables(path: Path, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    in_fence = False
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        # 区切り行を検出: 直前の行がヘッダ
        if SEPARATOR_RE.match(line) and i > 0:
            sep_cols = line.count("|") - (1 if line.lstrip().startswith("|") else 0) - (1 if line.rstrip().endswith("|") else 0)
            # より単純: パイプ数で区切ると壊れる → セル数を行から計算
            sep_cells = _count_cells(line)
            header_cells = _count_cells(lines[i - 1]) if i > 0 else 0
            if header_cells != sep_cells:
                findings.append(
                    Finding(path, i + 1, f"表ヘッダと区切り行の列数不一致 (header={header_cells}, sep={sep_cells})")
                )
            # 続く本体行を検査
            j = i + 1
            while j < n:
                body = lines[j]
                bs = body.lstrip()
                if not bs.startswith("|"):
                    break
                if bs.startswith("```") or bs.startswith("~~~"):
                    break
                body_cells = _count_cells(body)
                if body_cells != sep_cells:
                    findings.append(
                        Finding(path, j + 1, f"表本体の列数が不一致 (expected={sep_cells}, actual={body_cells})")
                    )
                j += 1
            i = j
            continue
        i += 1
    return findings


def _count_cells(line: str) -> int:
    """テーブル行のセル数を数える。前後の `|` は区切り扱いせずセル境界として数える。"""
    s = line.strip()
    # インラインコード内の | はテーブル区切りではないため除外
    s = re.sub(r"`[^`]*`", " ", s)
    if not s.startswith("|"):
        s = "|" + s
    if not s.endswith("|"):
        s = s + "|"
    # `\|` (エスケープ) は除外
    s2 = s.replace(r"\|", "\x00")
    return s2.count("|") - 1


def check():
    findings: list[Finding] = []
    for path in iter_files(extensions=[".md"]):
        lines = read_lines(path)
        findings.extend(check_fences(path, lines))
        findings.extend(check_link_brackets(path, lines))
        findings.extend(check_tables(path, lines))
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
