"""Quality Scorer のユニットテスト (Phase 3 拡充).

対応 ID: FUN-00302, NFR-00202, SCR-00001, SCR-00002, SCR-00101, SCR-00102,
SCR-00103, SCR-00104, SCR-00105, SCR-00106, SCR-00107, SCR-00201, SCR-00202
"""

from __future__ import annotations

import unittest

from local_llm_benchmark.scoring import (
    SCORING_FAILURE_KIND,
    ContainsScorer,
    ExactMatchScorer,
    JsonValidScorer,
    LengthWithinScorer,
    NormalizedMatchScorer,
    NumericCloseScorer,
    RegexMatchScorer,
    get_scorer,
    is_known_scorer,
    known_scorer_names,
)


class TestExactMatchScorer(unittest.TestCase):
    """SCR-00101 exact_match の最小ふるまい."""

    def setUp(self) -> None:
        self.scorer = ExactMatchScorer()

    def test_perfect_match_returns_one(self) -> None:
        r = self.scorer.score("answer", "answer", {})
        self.assertEqual(r.score, 1.0)
        self.assertIsNone(r.failure_kind)

    def test_mismatch_returns_zero(self) -> None:
        self.assertEqual(self.scorer.score("foo", "bar", {}).score, 0.0)

    def test_normalize_whitespace(self) -> None:
        r = self.scorer.score(
            "hello   world",
            "hello world",
            {"normalize_whitespace": True},
        )
        self.assertEqual(r.score, 1.0)

    def test_case_insensitive(self) -> None:
        r = self.scorer.score("Yes", "yes", {"case_insensitive": True})
        self.assertEqual(r.score, 1.0)

    def test_missing_expected_returns_unapplicable(self) -> None:
        r = self.scorer.score("anything", None, {})
        self.assertIsNone(r.score)
        self.assertEqual(r.failure_kind, SCORING_FAILURE_KIND)


class TestNormalizedMatchScorer(unittest.TestCase):
    """SCR-00102 normalized_match."""

    def setUp(self) -> None:
        self.scorer = NormalizedMatchScorer()

    def test_default_normalization_matches(self) -> None:
        # 既定で casefold + strip + collapse_whitespace + NFKC
        r = self.scorer.score("  Hello  WORLD  ", "hello world", {})
        self.assertEqual(r.score, 1.0)

    def test_full_width_collapsed_via_nfkc(self) -> None:
        # 全角英数 -> 半角 (NFKC)
        r = self.scorer.score("ＡＢＣ１２３", "abc123", {})
        self.assertEqual(r.score, 1.0)

    def test_disable_case_insensitive(self) -> None:
        r = self.scorer.score("Yes", "yes", {"case_insensitive": False})
        self.assertEqual(r.score, 0.0)

    def test_invalid_unicode_form_unapplicable(self) -> None:
        r = self.scorer.score("a", "a", {"unicode_form": "BOGUS"})
        self.assertIsNone(r.score)
        self.assertEqual(r.failure_kind, SCORING_FAILURE_KIND)

    def test_missing_expected_unapplicable(self) -> None:
        r = self.scorer.score("a", None, {})
        self.assertIsNone(r.score)


class TestRegexMatchScorer(unittest.TestCase):
    """SCR-00103 regex_match."""

    def setUp(self) -> None:
        self.scorer = RegexMatchScorer()

    def test_fullmatch_default(self) -> None:
        self.assertEqual(self.scorer.score("abc123", r"[a-z]+\d+", {}).score, 1.0)
        # fullmatch なので部分一致は 0.0
        self.assertEqual(self.scorer.score("xx abc123", r"[a-z]+\d+", {}).score, 0.0)

    def test_search_mode(self) -> None:
        r = self.scorer.score("xx abc123", r"[a-z]+\d+", {"mode": "search"})
        self.assertEqual(r.score, 1.0)

    def test_ignorecase_flag(self) -> None:
        r = self.scorer.score("ABC", r"abc", {"flags": ["IGNORECASE"]})
        self.assertEqual(r.score, 1.0)

    def test_invalid_pattern_unapplicable(self) -> None:
        r = self.scorer.score("x", r"(", {})
        self.assertIsNone(r.score)
        self.assertEqual(r.failure_kind, SCORING_FAILURE_KIND)

    def test_unknown_flag_unapplicable(self) -> None:
        r = self.scorer.score("x", r"x", {"flags": ["BOGUS"]})
        self.assertIsNone(r.score)

    def test_missing_pattern_unapplicable(self) -> None:
        self.assertIsNone(self.scorer.score("x", None, {}).score)


class TestContainsScorer(unittest.TestCase):
    """SCR-00104 contains."""

    def setUp(self) -> None:
        self.scorer = ContainsScorer()

    def test_single_substring_via_expected(self) -> None:
        self.assertEqual(self.scorer.score("hello world", "world", {}).score, 1.0)
        self.assertEqual(self.scorer.score("hello world", "xyz", {}).score, 0.0)

    def test_all_mode(self) -> None:
        r = self.scorer.score(
            "alpha beta gamma", None, {"substrings": ["alpha", "gamma"]}
        )
        self.assertEqual(r.score, 1.0)
        r2 = self.scorer.score(
            "alpha beta", None, {"substrings": ["alpha", "gamma"], "mode": "all"}
        )
        self.assertEqual(r2.score, 0.0)

    def test_any_mode(self) -> None:
        r = self.scorer.score(
            "only alpha", None, {"substrings": ["alpha", "gamma"], "mode": "any"}
        )
        self.assertEqual(r.score, 1.0)

    def test_case_insensitive(self) -> None:
        r = self.scorer.score(
            "HELLO", None,
            {"substrings": ["hello"], "case_insensitive": True},
        )
        self.assertEqual(r.score, 1.0)

    def test_empty_substrings_unapplicable(self) -> None:
        r = self.scorer.score("x", None, {"substrings": []})
        self.assertIsNone(r.score)

    def test_invalid_mode_unapplicable(self) -> None:
        r = self.scorer.score("x", "x", {"mode": "weird"})
        self.assertIsNone(r.score)

    def test_no_substrings_no_expected_unapplicable(self) -> None:
        self.assertIsNone(self.scorer.score("x", None, {}).score)


class TestJsonValidScorer(unittest.TestCase):
    """SCR-00105 json_valid."""

    def setUp(self) -> None:
        self.scorer = JsonValidScorer()

    def test_valid_json_object(self) -> None:
        self.assertEqual(self.scorer.score('{"a":1}', None, {}).score, 1.0)

    def test_invalid_json(self) -> None:
        self.assertEqual(self.scorer.score("not json", None, {}).score, 0.0)

    def test_require_object_rejects_array(self) -> None:
        r = self.scorer.score("[1,2,3]", None, {"require_object": True})
        self.assertEqual(r.score, 0.0)

    def test_require_array_accepts_array(self) -> None:
        r = self.scorer.score("[1,2,3]", None, {"require_array": True})
        self.assertEqual(r.score, 1.0)

    def test_required_keys_present(self) -> None:
        r = self.scorer.score(
            '{"a": 1, "b": 2}', None,
            {"require_object": True, "required_keys": ["a", "b"]},
        )
        self.assertEqual(r.score, 1.0)

    def test_required_keys_missing(self) -> None:
        r = self.scorer.score(
            '{"a": 1}', None, {"required_keys": ["a", "b"]},
        )
        self.assertEqual(r.score, 0.0)

    def test_conflicting_options_unapplicable(self) -> None:
        r = self.scorer.score(
            "{}", None, {"require_object": True, "require_array": True},
        )
        self.assertIsNone(r.score)


class TestLengthWithinScorer(unittest.TestCase):
    """SCR-00106 length_within."""

    def setUp(self) -> None:
        self.scorer = LengthWithinScorer()

    def test_chars_inside_range(self) -> None:
        r = self.scorer.score("abcde", None, {"min": 3, "max": 5})
        self.assertEqual(r.score, 1.0)

    def test_chars_below_min(self) -> None:
        r = self.scorer.score("ab", None, {"min": 3})
        self.assertEqual(r.score, 0.0)

    def test_chars_above_max(self) -> None:
        r = self.scorer.score("abcdef", None, {"max": 5})
        self.assertEqual(r.score, 0.0)

    def test_words_unit(self) -> None:
        r = self.scorer.score(
            "one two three four", None, {"unit": "words", "min": 2, "max": 5},
        )
        self.assertEqual(r.score, 1.0)

    def test_boundary_inclusive(self) -> None:
        # min 境界
        self.assertEqual(self.scorer.score("abc", None, {"min": 3}).score, 1.0)
        # max 境界
        self.assertEqual(self.scorer.score("abc", None, {"max": 3}).score, 1.0)

    def test_no_bounds_unapplicable(self) -> None:
        self.assertIsNone(self.scorer.score("x", None, {}).score)

    def test_min_greater_than_max_unapplicable(self) -> None:
        r = self.scorer.score("x", None, {"min": 5, "max": 3})
        self.assertIsNone(r.score)

    def test_unknown_unit_unapplicable(self) -> None:
        self.assertIsNone(
            self.scorer.score("x", None, {"unit": "bytes", "min": 1}).score
        )


class TestNumericCloseScorer(unittest.TestCase):
    """SCR-00107 numeric_close."""

    def setUp(self) -> None:
        self.scorer = NumericCloseScorer()

    def test_exact_numeric_match(self) -> None:
        self.assertEqual(self.scorer.score("42", "42", {}).score, 1.0)

    def test_within_abs_tolerance(self) -> None:
        r = self.scorer.score("42.5", "42", {"abs_tol": 0.6})
        self.assertEqual(r.score, 1.0)

    def test_outside_abs_tolerance(self) -> None:
        r = self.scorer.score("42.5", "42", {"abs_tol": 0.1})
        self.assertEqual(r.score, 0.0)

    def test_within_rel_tolerance(self) -> None:
        # rel_tol=0.05, expected=100, actual=104 → diff=4 <= 5
        r = self.scorer.score("104", "100", {"rel_tol": 0.05})
        self.assertEqual(r.score, 1.0)

    def test_extract_first_from_text(self) -> None:
        r = self.scorer.score("答えは 42 です", "42", {})
        self.assertEqual(r.score, 1.0)

    def test_extract_last(self) -> None:
        r = self.scorer.score("初項は 1, 答えは 42", "42", {"extract": "last"})
        self.assertEqual(r.score, 1.0)

    def test_extract_strict_with_text_returns_zero(self) -> None:
        r = self.scorer.score("答えは 42", "42", {"extract": "strict"})
        self.assertEqual(r.score, 0.0)

    def test_no_number_returns_zero(self) -> None:
        r = self.scorer.score("no digits here", "1", {})
        self.assertEqual(r.score, 0.0)

    def test_negative_tolerance_unapplicable(self) -> None:
        r = self.scorer.score("1", "1", {"abs_tol": -0.1})
        self.assertIsNone(r.score)

    def test_expected_arg_overrides(self) -> None:
        r = self.scorer.score("3.14", None, {"expected": 3.14})
        self.assertEqual(r.score, 1.0)

    def test_no_expected_unapplicable(self) -> None:
        self.assertIsNone(self.scorer.score("1", None, {}).score)


class TestRegistry(unittest.TestCase):
    def test_get_all_known_scorers(self) -> None:
        names = known_scorer_names()
        # SCR-00101..00107 すべて登録されていること
        for n in (
            "exact_match",
            "normalized_match",
            "regex_match",
            "contains",
            "json_valid",
            "length_within",
            "numeric_close",
        ):
            self.assertIn(n, names)
            self.assertTrue(is_known_scorer(n))
            # 解決可能であること (例外が出ないことを確認)
            get_scorer(n)

    def test_unknown_scorer_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_scorer("does-not-exist")
        self.assertFalse(is_known_scorer("does-not-exist"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
