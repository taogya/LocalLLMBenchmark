"""
TASK-00004-03: トレーサビリティ機械チェック群の共通ヘルパー。

- ID 抽出 (`<Prefix>-NNNNN` 形式) や走査対象ファイルの列挙、結果出力フォーマットを集約する。
- Python 標準ライブラリのみで構成 (NFR-00302)。
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


# リポジトリルート (scripts/traceability/_common.py から見て 2 つ上)
REPO_ROOT = Path(__file__).resolve().parents[2]


# ID パターン
ID_PATTERN = re.compile(r"\b([A-Z]+)-(\d{5})\b")
# 桁数違反などの "ID っぽい" 文字列。 [A-Z] 1 文字以上 + ハイフン + 数字 1 桁以上
LOOSE_ID_PATTERN = re.compile(r"\b([A-Za-z]+)-(\d+)\b")
# 既知の prefix。これに該当する loose 一致を format 検査の対象にする。
KNOWN_PREFIXES = {
    "REQ", "FUN", "NFR", "OOS",
    "ARCH", "COMP", "DAT", "FLW",
    "CLI", "CFG", "PVD", "SCR",
    "ROLE", "PROG", "TASK", "TRC",
}


# 走査対象トップレベル
DEFAULT_SCAN_DIRS = [
    "docs",
    "progress",
    "src",
    "tests",
    "configs",
    "prompts",
    ".github",
    "scripts",
]
DEFAULT_SCAN_FILES = ["README.md"]

# 除外ディレクトリ (パス先頭一致)
EXCLUDE_DIRS_PREFIXES = (
    ".git/",
    ".venv/",
    "node_modules/",
    "tmp/",
    "progress/v0.1.0/",
    "v0.1.0/",
)


# implementation-leak チェックで除外したい用語 / 文脈
IMPL_LEAK_WHITELIST_TERMS = {
    # 標準ライブラリの言及自体は許容
    "tomllib", "statistics", "pathlib", "argparse",  # メタ言及のみ許容
}

# 各 prefix の正本 (canonical) 文書 (リポジトリルート相対パス, 接頭辞一致)
# 同一 prefix の ID はこの文書配下にあるものを「定義」として扱う。
CANONICAL_DEF_DOCS: dict[str, tuple[str, ...]] = {
    "REQ": ("docs/requirements/01-overview.md",),
    "FUN": ("docs/requirements/02-functional.md",),
    "NFR": ("docs/requirements/03-non-functional.md",),
    "OOS": ("docs/requirements/04-out-of-scope.md",),
    "ARCH": ("docs/design/01-architecture.md",),
    "COMP": ("docs/design/02-components.md",),
    "DAT": ("docs/design/03-data-model.md",),
    "FLW": ("docs/design/04-workflows.md",),
    "CLI": ("docs/design/05-cli-surface.md",),
    "CFG": ("docs/design/06-configuration-sources.md",),
    "PVD": ("docs/design/07-provider-contract.md",),
    "SCR": ("docs/design/08-scoring-and-ranking.md",),
    "ROLE": ("docs/development/roles.md",),
    "PROG": ("docs/development/progress.md",),
    "TRC": ("docs/development/traceability.md",),
    # TASK は progress/ 配下のファイル名で別途扱う
}


def is_canonical_def_path(prefix: str, path: Path) -> bool:
    """path がその prefix の正本ドキュメントか判定する。"""
    canonicals = CANONICAL_DEF_DOCS.get(prefix)
    if not canonicals:
        return False
    rel = path.relative_to(REPO_ROOT).as_posix() if path.is_absolute() else path.as_posix()
    return rel in canonicals


@dataclass
class Finding:
    """違反情報。"""
    file: Path
    line: int
    reason: str

    def format(self) -> str:
        rel = self.file.relative_to(REPO_ROOT) if self.file.is_absolute() else self.file
        return f"[FAIL] {rel}:{self.line}: {self.reason}"


def iter_files(
    extensions: Iterable[str] | None = None,
    include_dirs: Iterable[str] | None = None,
    include_files: Iterable[str] | None = None,
) -> Iterator[Path]:
    """走査対象ファイルを列挙する。

    extensions: 拡張子フィルタ (例 [".md"])。None なら全拡張子。
    include_dirs: 走査対象ディレクトリ (リポジトリルート相対)。
    include_files: 走査対象ファイル (リポジトリルート相対)。
    """
    if include_dirs is None:
        include_dirs = DEFAULT_SCAN_DIRS
    if include_files is None:
        include_files = DEFAULT_SCAN_FILES

    seen: set[Path] = set()
    ext_set = {e.lower() for e in extensions} if extensions else None

    for d in include_dirs:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(prefix) for prefix in EXCLUDE_DIRS_PREFIXES):
                continue
            # tmp/ 配下は除外 (入れ子も)
            if "/tmp/" in f"/{rel}":
                continue
            if ext_set is not None and p.suffix.lower() not in ext_set:
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p

    for f in include_files:
        p = REPO_ROOT / f
        if not p.exists() or not p.is_file():
            continue
        if ext_set is not None and p.suffix.lower() not in ext_set:
            continue
        if p in seen:
            continue
        seen.add(p)
        yield p


def read_lines(path: Path) -> list[str]:
    """ファイル全体を行単位で読む (改行は保持しない)。"""
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        # バイナリは読み飛ばし
        return []


def extract_ids(text: str) -> list[tuple[str, int]]:
    """テキストから ID を抽出する (prefix, 数値) のリスト。"""
    return [(m.group(1), int(m.group(2))) for m in ID_PATTERN.finditer(text)]


def report(findings: list[Finding]) -> int:
    """違反一覧を出力し、終了コードを返す。"""
    if not findings:
        print("OK")
        return 0
    for f in findings:
        print(f.format())
    print(f"[FAIL] total={len(findings)}")
    return 1


def main_wrapper(check_func) -> int:
    """各 check スクリプトの main で使う共通エントリ。"""
    findings = list(check_func())
    return report(findings)


def is_table_definition_line(line: str) -> str | None:
    """テーブル行 `| ID-00001 | ... |` の先頭セルから ID を返す。"""
    m = re.match(r"^\s*\|\s*([A-Z]+-\d{5})\b", line)
    if m:
        return m.group(1)
    return None


def is_heading_definition_line(line: str) -> list[str]:
    """見出し行から ID を抽出する。"""
    m = re.match(r"^\s*#{1,6}\s+(.*)$", line)
    if not m:
        return []
    return [f"{p}-{n:05d}" for p, n in extract_ids(m.group(1))]


def collect_definitions(paths: Iterable[Path], canonical_only: bool = True) -> dict[str, list[Finding]]:
    """定義として認識される ID と、その出現位置一覧を返す。

    canonical_only=True (既定) の場合、CANONICAL_DEF_DOCS にマッチする
    ファイル配下の出現のみを定義として扱う。これは「再掲表」(release-criteria
    のような参照テーブル) と「正本」を区別するため。
    """
    defs: dict[str, list[Finding]] = {}
    for p in paths:
        for i, line in enumerate(read_lines(p), start=1):
            tid = is_table_definition_line(line)
            if tid:
                prefix = tid.split("-", 1)[0]
                if canonical_only and not is_canonical_def_path(prefix, p):
                    continue
                defs.setdefault(tid, []).append(Finding(p, i, "table"))
                continue
            for hid in is_heading_definition_line(line):
                prefix = hid.split("-", 1)[0]
                if canonical_only and not is_canonical_def_path(prefix, p):
                    continue
                defs.setdefault(hid, []).append(Finding(p, i, "heading"))
    return defs


def strip_inline_code_and_links(line: str) -> str:
    """`...` のインラインコードとリンクテキスト [..](..) を取り除いた文字列を返す。"""
    # インラインコード
    line = re.sub(r"`[^`]*`", " ", line)
    return line


def in_fenced_code_blocks(lines: list[str]) -> list[bool]:
    """各行がコードフェンス内かどうかを返す。"""
    flags = [False] * len(lines)
    in_block = False
    for i, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            in_block = not in_block
            flags[i] = True  # フェンス行自体は内側扱い
            continue
        flags[i] = in_block
    return flags


__all__ = [
    "REPO_ROOT",
    "ID_PATTERN",
    "LOOSE_ID_PATTERN",
    "KNOWN_PREFIXES",
    "Finding",
    "iter_files",
    "read_lines",
    "extract_ids",
    "report",
    "main_wrapper",
    "is_table_definition_line",
    "is_heading_definition_line",
    "collect_definitions",
    "strip_inline_code_and_links",
    "in_fenced_code_blocks",
    "IMPL_LEAK_WHITELIST_TERMS",
    "CANONICAL_DEF_DOCS",
    "is_canonical_def_path",
]
