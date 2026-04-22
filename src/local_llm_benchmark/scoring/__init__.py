"""Quality Scorer 群 (TASK-00007-01 / TASK-00007-03).

COMP-00006 / SCR- 系を担う。Phase 3 で SCR-00101..00107 をすべて実装する。

設計原則:
- SCR-00001 決定的 (LLM-as-a-Judge は持たない)
- SCR-00002 出力は [0.0, 1.0] または bool (集計時に 0.0/1.0)
- SCR-00201 入力は応答テキストと期待出力のみ。生応答は渡さない
- SCR-00202 失敗は例外で表現せず PVD-00307 相当 (`scoring 適用不可`) を返す
- SCR-00203 bool を返す scorer は集計時に 0.0/1.0 として扱う
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


SCORING_FAILURE_KIND = "scoring_unapplicable"  # PVD-00307


@dataclass(frozen=True)
class ScoreResult:
    """採点結果.

    score が None の場合は採点不可 (failure_detail に理由)。
    """

    score: float | None
    failure_kind: str | None = None
    failure_detail: str | None = None


class Scorer(Protocol):  # pragma: no cover - 構造的型
    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult: ...


def _unapplicable(detail: str) -> ScoreResult:
    return ScoreResult(
        score=None,
        failure_kind=SCORING_FAILURE_KIND,
        failure_detail=detail,
    )


# ---- SCR-00101 exact_match -------------------------------------------------


class ExactMatchScorer:
    """SCR-00101 exact_match.

    期待文字列 1 件に対する厳密一致。任意で `normalize_whitespace` /
    `case_insensitive` を引数で受け取る (SCR-00102 の軽量版相当)。
    """

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        if expected_output is None:
            return _unapplicable("exact_match は expected_output を必須とする")
        actual = response_text
        expected = expected_output
        if args.get("normalize_whitespace"):
            actual = " ".join(actual.split())
            expected = " ".join(expected.split())
        if args.get("case_insensitive"):
            actual = actual.lower()
            expected = expected.lower()
        return ScoreResult(score=1.0 if actual == expected else 0.0)


# ---- SCR-00102 normalized_match -------------------------------------------


class NormalizedMatchScorer:
    """SCR-00102 normalized_match.

    期待文字列 1 件 + 正規化方針 (大小文字 / 前後空白 / 全半角畳み込み)
    を吸収した一致を判定する。

    引数:
        case_insensitive (bool, 既定 True)
        strip (bool, 既定 True): 前後空白の除去
        collapse_whitespace (bool, 既定 True): 連続空白の畳み込み
        unicode_form (str, 既定 "NFKC"): 全半角畳み込み等の正規化形
    """

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        if expected_output is None:
            return _unapplicable("normalized_match は expected_output を必須とする")
        case_insensitive = bool(args.get("case_insensitive", True))
        do_strip = bool(args.get("strip", True))
        collapse_ws = bool(args.get("collapse_whitespace", True))
        form = str(args.get("unicode_form", "NFKC"))
        if form not in ("NFC", "NFD", "NFKC", "NFKD"):
            return _unapplicable(f"未知の unicode_form: {form}")

        def _norm(s: str) -> str:
            s = unicodedata.normalize(form, s)
            if do_strip:
                s = s.strip()
            if collapse_ws:
                s = " ".join(s.split())
            if case_insensitive:
                s = s.casefold()
            return s

        return ScoreResult(
            score=1.0 if _norm(response_text) == _norm(expected_output) else 0.0
        )


# ---- SCR-00103 regex_match ------------------------------------------------


class RegexMatchScorer:
    """SCR-00103 regex_match.

    正規表現 1 件で応答テキストを判定する。

    引数:
        flags (list[str], 任意): "I"/"IGNORECASE", "M"/"MULTILINE",
            "S"/"DOTALL", "X"/"VERBOSE" を受け付ける
        mode (str, 既定 "fullmatch"): "fullmatch" / "search" / "match"
    """

    _FLAG_ALIASES: Mapping[str, int] = {
        "I": re.IGNORECASE, "IGNORECASE": re.IGNORECASE,
        "M": re.MULTILINE, "MULTILINE": re.MULTILINE,
        "S": re.DOTALL, "DOTALL": re.DOTALL,
        "X": re.VERBOSE, "VERBOSE": re.VERBOSE,
    }

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        if expected_output is None:
            return _unapplicable("regex_match は expected_output (正規表現) を必須とする")
        flag_value = 0
        for raw in args.get("flags") or []:
            f = self._FLAG_ALIASES.get(str(raw).upper())
            if f is None:
                return _unapplicable(f"未知の regex フラグ: {raw}")
            flag_value |= f
        mode = str(args.get("mode", "fullmatch"))
        if mode not in ("fullmatch", "search", "match"):
            return _unapplicable(f"未知の regex mode: {mode}")
        try:
            pattern = re.compile(expected_output, flag_value)
        except re.error as exc:
            return _unapplicable(f"正規表現コンパイル失敗: {exc}")
        m = getattr(pattern, mode)(response_text)
        return ScoreResult(score=1.0 if m else 0.0)


# ---- SCR-00104 contains ---------------------------------------------------


class ContainsScorer:
    """SCR-00104 contains.

    期待部分文字列 1 件以上を AND または OR で判定する。

    引数:
        substrings (list[str], 必須): 1 件以上の部分文字列。
            未指定時は expected_output を単一要素として扱う。
        mode (str, 既定 "all"): "all" (AND) / "any" (OR)
        case_insensitive (bool, 既定 False)
    """

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        subs_arg = args.get("substrings")
        substrings: list[str]
        if subs_arg is None:
            if expected_output is None:
                return _unapplicable(
                    "contains は substrings または expected_output を必須とする"
                )
            substrings = [expected_output]
        elif isinstance(subs_arg, (list, tuple)):
            substrings = [str(s) for s in subs_arg]
        else:
            return _unapplicable("contains.substrings は配列で指定する")
        if not substrings:
            return _unapplicable("contains.substrings は 1 件以上必要")
        mode = str(args.get("mode", "all"))
        if mode not in ("all", "any"):
            return _unapplicable(f"未知の contains mode: {mode}")
        case_insensitive = bool(args.get("case_insensitive", False))
        haystack = response_text.lower() if case_insensitive else response_text
        needles = [s.lower() if case_insensitive else s for s in substrings]
        results = [n in haystack for n in needles]
        ok = all(results) if mode == "all" else any(results)
        return ScoreResult(score=1.0 if ok else 0.0)


# ---- SCR-00105 json_valid -------------------------------------------------


class JsonValidScorer:
    """SCR-00105 json_valid.

    応答テキストが JSON として妥当かを判定する。

    引数:
        require_object (bool, 既定 False): トップレベルが object であること
        require_array (bool, 既定 False): トップレベルが array であること
        required_keys (list[str], 任意): require_object と併用。
            トップレベル object に当該キーがすべて存在することを要求する
            (期待スキーマの最小表現)。
    """

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        require_object = bool(args.get("require_object", False))
        require_array = bool(args.get("require_array", False))
        if require_object and require_array:
            return _unapplicable("require_object と require_array は同時指定不可")
        try:
            parsed = json.loads(response_text)
        except (ValueError, TypeError):
            return ScoreResult(score=0.0)
        if require_object and not isinstance(parsed, dict):
            return ScoreResult(score=0.0)
        if require_array and not isinstance(parsed, list):
            return ScoreResult(score=0.0)
        required_keys = args.get("required_keys") or []
        if required_keys:
            if not isinstance(parsed, dict):
                return ScoreResult(score=0.0)
            for key in required_keys:
                if str(key) not in parsed:
                    return ScoreResult(score=0.0)
        return ScoreResult(score=1.0)


# ---- SCR-00106 length_within ----------------------------------------------


class LengthWithinScorer:
    """SCR-00106 length_within.

    応答テキストの長さ (文字数または語数) が範囲 [min, max] に
    収まるかを判定する。

    引数:
        unit (str, 既定 "chars"): "chars" / "words"
        min (int, 任意): 下限 (含む)
        max (int, 任意): 上限 (含む)

    min と max のいずれか 1 つ以上が必須。
    """

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        unit = str(args.get("unit", "chars"))
        if unit not in ("chars", "words"):
            return _unapplicable(f"未知の length_within unit: {unit}")
        lower = args.get("min")
        upper = args.get("max")
        if lower is None and upper is None:
            return _unapplicable(
                "length_within は min または max のいずれかを必須とする"
            )
        try:
            lo = None if lower is None else int(lower)
            hi = None if upper is None else int(upper)
        except (TypeError, ValueError):
            return _unapplicable("length_within の min/max は整数を指定する")
        if lo is not None and hi is not None and lo > hi:
            return _unapplicable("length_within: min > max は不正")
        length = (
            len(response_text) if unit == "chars" else len(response_text.split())
        )
        if lo is not None and length < lo:
            return ScoreResult(score=0.0)
        if hi is not None and length > hi:
            return ScoreResult(score=0.0)
        return ScoreResult(score=1.0)


# ---- SCR-00107 numeric_close ----------------------------------------------


class NumericCloseScorer:
    """SCR-00107 numeric_close.

    応答テキストから抽出した数値と期待数値が、絶対差または相対差の
    許容範囲内に収まるかを判定する。

    引数:
        expected (float, 任意): 期待数値。未指定時は expected_output を
            float として解釈する。
        abs_tol (float, 任意): 絶対誤差の上限 (既定 0.0)
        rel_tol (float, 任意): 相対誤差の上限 (既定 0.0)
        extract (str, 既定 "first"): 応答テキストからの数値抽出方針。
            "first" / "last" / "strict" (応答全体が数値表現のみ)
    """

    _NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")

    def score(
        self,
        response_text: str,
        expected_output: str | None,
        args: Mapping[str, Any],
    ) -> ScoreResult:
        if "expected" in args and args["expected"] is not None:
            try:
                expected = float(args["expected"])
            except (TypeError, ValueError):
                return _unapplicable(
                    "numeric_close.expected が float に変換できない"
                )
        elif expected_output is not None:
            try:
                expected = float(expected_output)
            except (TypeError, ValueError):
                return _unapplicable(
                    "numeric_close は expected_output を float として"
                    "解釈できる必要がある"
                )
        else:
            return _unapplicable(
                "numeric_close は expected または expected_output を必須とする"
            )

        try:
            abs_tol = float(args.get("abs_tol", 0.0))
            rel_tol = float(args.get("rel_tol", 0.0))
        except (TypeError, ValueError):
            return _unapplicable(
                "numeric_close の abs_tol / rel_tol は float を指定する"
            )
        if abs_tol < 0 or rel_tol < 0:
            return _unapplicable("numeric_close の許容差は 0 以上を指定する")

        extract = str(args.get("extract", "first"))
        if extract not in ("first", "last", "strict"):
            return _unapplicable(f"未知の numeric_close extract: {extract}")

        text = response_text.strip()
        if extract == "strict":
            try:
                actual = float(text)
            except (TypeError, ValueError):
                return ScoreResult(score=0.0)
        else:
            matches = self._NUM_RE.findall(text)
            if not matches:
                return ScoreResult(score=0.0)
            token = matches[0] if extract == "first" else matches[-1]
            try:
                actual = float(token)
            except ValueError:
                return ScoreResult(score=0.0)

        diff = abs(actual - expected)
        tol = max(abs_tol, rel_tol * abs(expected))
        return ScoreResult(score=1.0 if diff <= tol else 0.0)


# ---- レジストリ ------------------------------------------------------------


_REGISTRY: dict[str, Callable[[], Scorer]] = {
    "exact_match": ExactMatchScorer,           # SCR-00101
    "normalized_match": NormalizedMatchScorer, # SCR-00102
    "regex_match": RegexMatchScorer,           # SCR-00103
    "contains": ContainsScorer,                # SCR-00104
    "json_valid": JsonValidScorer,             # SCR-00105
    "length_within": LengthWithinScorer,       # SCR-00106
    "numeric_close": NumericCloseScorer,       # SCR-00107
}


def get_scorer(name: str) -> Scorer:
    """名前から scorer を解決する (CFG-00503).

    未登録名は ConfigurationError 相当の ValueError で報告。
    """
    factory = _REGISTRY.get(name)
    if factory is None:
        raise ValueError(
            f"未登録の scorer: {name} (登録済み: {sorted(_REGISTRY)})"
        )
    return factory()


def known_scorer_names() -> list[str]:
    return sorted(_REGISTRY)


def is_known_scorer(name: str) -> bool:
    """設定検証 (CFG-00503) 用の問い合わせ窓口."""
    return name in _REGISTRY
