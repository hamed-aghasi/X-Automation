import json
import unittest
from pathlib import Path

from xr import x_text

FIXTURE = Path(__file__).parent / "fixtures" / "twitter_text_v3_weighted.json"


class ConformanceTest(unittest.TestCase):
    def test_v3_conformance_cases(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertIn("Apache-2.0", data["_source"]["licence"])
        self.assertEqual(len(data["cases"]), 22)
        for case in data["cases"]:
            with self.subTest(case["description"]):
                self.assertEqual(x_text.weighted_length(case["text"]), case["weightedLength"])
                self.assertEqual(x_text.check(case["text"])["valid"], case["valid"])


class PersianTest(unittest.TestCase):
    def test_letters_count_one(self):
        self.assertEqual(x_text.weighted_length("سلام"), 4)

    def test_zwnj_counts_one(self):
        word = "می\u200cخواهم"
        self.assertEqual(len(word), 8)
        self.assertEqual(x_text.weighted_length(word), 8)

    def test_persian_digits_count_one(self):
        self.assertEqual(x_text.weighted_length("۱۴۰۵"), 4)

    def test_rlm_counts_two(self):
        self.assertEqual(x_text.weighted_length("a\u200fb"), 4)

    def test_280_letters_valid_281_not(self):
        ok = x_text.check("س" * 280)
        self.assertEqual(ok, {"weighted": 280, "valid": True, "remaining": 0, "reason": None})
        over = x_text.check("س" * 281)
        self.assertEqual(over, {"weighted": 281, "valid": False, "remaining": -1, "reason": "too_long"})

    def test_url_counts_23_in_mixed_text(self):
        text = "Claude Code را امتحان کنید https://example.com/very/long/path"
        self.assertEqual(x_text.weighted_length(text), 27 + 23)


class EmojiTest(unittest.TestCase):
    def test_skin_tone_sequence_is_two(self):
        self.assertEqual(x_text.weighted_length("👍🏽"), 2)

    def test_family_zwj_sequence_is_two(self):
        self.assertEqual(x_text.weighted_length("👨\u200d👩\u200d👧\u200d👦"), 2)


class CheckTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(x_text.check(""), {"weighted": 0, "valid": False, "remaining": 280, "reason": "empty"})

    def test_whitespace_only_is_empty(self):
        r = x_text.check("  \n\t ")
        self.assertFalse(r["valid"])
        self.assertEqual(r["reason"], "empty")

    def test_invalid_char(self):
        r = x_text.check("ABC\ufffeABC")
        self.assertFalse(r["valid"])
        self.assertEqual(r["reason"], "invalid_char")

    def test_max_constant(self):
        self.assertEqual(x_text.MAX_WEIGHTED, 280)


class CrlfTest(unittest.TestCase):
    def test_crlf_counts_two_at_boundary(self):
        text = "س" * 279 + "\r\n"
        self.assertEqual(x_text.weighted_length(text), 281)
        self.assertEqual(x_text.check(text), {"weighted": 281, "valid": False, "remaining": -1, "reason": "too_long"})

    def test_lone_lf_and_cr_count_one(self):
        self.assertEqual(x_text.weighted_length("a\nb"), 3)
        self.assertEqual(x_text.weighted_length("a\r\nb\r\nc"), 7)


class SurrogateTest(unittest.TestCase):
    def test_check_lone_surrogate_is_invalid_char(self):
        r = x_text.check("a\ud800b")
        self.assertFalse(r["valid"])
        self.assertEqual(r["reason"], "invalid_char")

    def test_weighted_length_lone_surrogate_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "lone surrogate"):
            x_text.weighted_length("a\udfffb")


if __name__ == "__main__":
    unittest.main()
