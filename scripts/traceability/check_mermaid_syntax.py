#!/usr/bin/env python3
"""
TASK-00004-03: Mermaid 構文の軽量検査。

- ` ```mermaid ` フェンス内を抽出
- 必ず検出: `<br/>` `<BR/>` `<Br/>` (Mermaid 標準でラベル内に書くと崩れることが多い)
- ヒューリスティック: `[]` `()` `{}` `<<` `>>` の対称性、矢印 `-->` `->>` `-.->` `==>` 等
- オプション: 環境変数 `MMDC` で mmdc バイナリ指定 / `which mmdc` が成功すれば実行
  - mmdc が無い / 失敗した場合は warn のみで失敗扱いにしない (既定挙動)
  - 環境変数 `MMDC_REQUIRED=1` がセットされている場合、mmdc 不在を FAIL として扱う
    (CI 等で mmdc 検証を必須化したいとき用)。TASK-00005-01 で追加。

mmdc CLI のインストール方法:
- macOS: `brew install mermaid-cli`
  - puppeteer が要求する Chrome 版が無い場合は
    `npx puppeteer browsers install chrome-headless-shell@<version>` を実行する。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from traceability._common import (  # noqa: E402
    Finding,
    iter_files,
    main_wrapper,
    read_lines,
)


BR_RE = re.compile(r"<br\s*/>", re.IGNORECASE)
ARROW_RE = re.compile(r"-->|->>|-\.->|==>|--x|-\.-|--o")


def extract_mermaid_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """ファイル内の mermaid コードブロックを (開始行番号, 行群) で返す。"""
    blocks: list[tuple[int, list[str]]] = []
    i = 0
    while i < len(lines):
        line = lines[i].lstrip()
        if line.startswith("```mermaid") or line.startswith("~~~mermaid"):
            start = i + 1
            body: list[str] = []
            i += 1
            while i < len(lines):
                if lines[i].lstrip().startswith("```") or lines[i].lstrip().startswith("~~~"):
                    break
                body.append(lines[i])
                i += 1
            blocks.append((start, body))
        i += 1
    return blocks


def check_block(path: Path, start_line: int, body: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for offset, line in enumerate(body):
        line_no = start_line + offset + 1
        if BR_RE.search(line):
            findings.append(
                Finding(path, line_no, "Mermaid 内に <br/> 系が含まれる (ラベル崩れの原因)")
            )
    # 全体での括弧バランス
    full = "\n".join(body)
    pairs = [("[", "]"), ("(", ")"), ("{", "}")]
    for open_c, close_c in pairs:
        if full.count(open_c) != full.count(close_c):
            findings.append(
                Finding(
                    path,
                    start_line,
                    f"Mermaid ブロックの '{open_c}{close_c}' 数が不一致 "
                    f"(open={full.count(open_c)}, close={full.count(close_c)})",
                )
            )
    # `<<` `>>` はシーケンス図の `->>` と評価が衝突するため `>>` だけでは判定しない。
    # `<<` が出現した場合のみ、クラス図のステレオタイプ表記としてペアを期待する。
    if full.count("<<") > 0 and full.count("<<") != full.count(">>"):
        findings.append(
            Finding(
                path,
                start_line,
                f"Mermaid ブロックの '<<' '>>' 数が不一致 "
                f"(<<={full.count('<<')}, >>={full.count('>>')})",
            )
        )
    return findings


def run_mmdc(path: Path, body: str, start_line: int) -> list[Finding]:
    mmdc = os.environ.get("MMDC") or shutil.which("mmdc")
    if not mmdc:
        return []
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "diagram.mmd"
        out = Path(td) / "diagram.svg"
        src.write_text(body, encoding="utf-8")
        try:
            res = subprocess.run(
                [mmdc, "-i", str(src), "-o", str(out)],
                capture_output=True, text=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[WARN] mmdc 実行失敗: {e} (スキップ)", file=sys.stderr)
            return []
        if res.returncode != 0:
            return [
                Finding(
                    path,
                    start_line,
                    f"mmdc が構文エラーを報告: {res.stderr.strip()[:200]}",
                )
            ]
    return []


def check():
    findings: list[Finding] = []
    mmdc_available = bool(os.environ.get("MMDC") or shutil.which("mmdc"))
    mmdc_required = os.environ.get("MMDC_REQUIRED") == "1"
    if not mmdc_available:
        if mmdc_required:
            # MMDC_REQUIRED=1 のときは mmdc 不在を FAIL に格上げ (TASK-00005-01)
            findings.append(
                Finding(
                    Path("."),
                    0,
                    "MMDC_REQUIRED=1 だが mmdc が見つからない (PATH または環境変数 MMDC で指定)",
                )
            )
            return findings
        print("[WARN] mmdc が見つからないため CLI 構文検証はスキップ", file=sys.stderr)
    for path in iter_files(extensions=[".md"]):
        lines = read_lines(path)
        for start, body in extract_mermaid_blocks(lines):
            findings.extend(check_block(path, start, body))
            if mmdc_available:
                findings.extend(run_mmdc(path, "\n".join(body), start))
    return findings


if __name__ == "__main__":
    sys.exit(main_wrapper(check))
