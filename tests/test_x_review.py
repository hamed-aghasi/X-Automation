import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.test_x_draft import URL_HN, StubLLM, topic
from xr import rank, x_cli, x_review, x_text

FIVES = {"accuracy": 5, "clarity": 5, "voice": 5, "platform_fit": 5}
PASS = {"issues": [], "scores": FIVES}
REVISE = {"issues": [{"rule": "T3", "severity": "blocking", "quote": "groundbreaking", "fix": "state the fact"}],
          "scores": {"accuracy": 4, "clarity": 3, "voice": 2, "platform_fit": 4}}
EN = f"Anthropic released Claude Opus 5.5. {URL_HN}"
FA = f"آنتروپیک مدل Claude Opus 5.5 را منتشر کرد. {URL_HN}"


def d(text, sid="e1"):
    return {"text": text, "source_id": sid}


def rules(out):
    return [i["rule"] for i in out["issues"]]


class GateTest(unittest.TestCase):
    def gated(self, lang, text, rule, source_url=None):
        llm = StubLLM()
        out = x_review.review(topic(), lang, text, llm=llm, source_url=source_url)
        self.assertEqual(out["verdict"], "revise")
        self.assertIn(rule, rules(out))
        self.assertTrue(all(i["severity"] == "blocking" for i in out["issues"]))
        self.assertEqual(llm.prompts, [])

    def test_too_long(self):
        self.gated("en", "a" * 257 + " " + URL_HN, "length")  # 257 + 1 + 23 = 281

    def test_urls_found_the_way_x_finds_them(self):
        for text in (f"Visit evil.com {URL_HN}", f"Visit HTTPS://evil.com/x {URL_HN}", f"News {URL_HN} {URL_HN}",
                     "News https://evil.example/x", f"News {URL_HN}/extra", "No link at all"):
            with self.subTest(text):
                self.gated("en", text, "url")

    def test_url_must_equal_returned_source_url(self):
        self.gated("en", "News https://reddit.com/r/ClaudeAI/comments/abc/opus", "url", source_url=URL_HN)

    def test_fa_opening_must_be_a_persian_letter(self):
        for text in (f"Claude Opus 5.5 منتشر شد. {URL_HN}", f"\u200fClaude منتشر شد. {URL_HN}",
                     f"\u061cClaude منتشر شد. {URL_HN}", f"۴۰ درصد ارزان‌تر شد. {URL_HN}",
                     f"40 درصد ارزان‌تر شد. {URL_HN}"):
            with self.subTest(text):
                self.gated("fa", text, "first-word")

    def test_fa_opening_skips_controls_and_punctuation(self):
        for text in (FA, "\u200f" + FA, "«" + FA):
            with self.subTest(text):
                self.assertTrue(x_review.opens_persian(text))

    def test_fa_dashes(self):
        for ch in ("—", "–"):
            with self.subTest(ch):
                self.gated("fa", f"آنتروپیک {ch} مدل تازه. {URL_HN}", "dash")

    def test_clean_text_goes_to_llm_with_check_and_fa_issues(self):
        llm = StubLLM(reviews=[PASS])
        out = x_review.review(topic(), "fa", FA, llm=llm, source_url=URL_HN)
        self.assertEqual(out["verdict"], "pass")
        p = llm.prompts[0]
        self.assertIn('"weighted"', p)
        self.assertIn("<topic>", p)
        self.assertIn("<persian_writing_guide>", p)
        self.assertIn("An analysis\n   of 15,465 public MCP servers found", p)


class DecideTest(unittest.TestCase):
    def verdict(self, reply):
        return x_review.review(topic(), "en", EN, llm=StubLLM(reviews=[reply]))["verdict"]

    def test_code_decides_the_verdict(self):
        blocking = [{"rule": "accuracy", "severity": "blocking", "quote": "q", "fix": "f"}]
        minor = [{"rule": "voice", "severity": "minor", "quote": "q", "fix": "f"}]
        cases = [
            ({"verdict": "pass", "issues": blocking, "scores": FIVES}, "revise"),  # contradictory reply
            ({"issues": [], "scores": {**FIVES, "accuracy": 3}}, "revise"),
            ({"issues": [], "scores": {**FIVES, "clarity": 2}}, "revise"),
            ({"issues": [], "scores": {"accuracy": 5}}, "revise"),  # missing scores count as 0
            ({"issues": minor, "scores": {**FIVES, "voice": 3}}, "pass"),
            (PASS, "pass"),
        ]
        for reply, want in cases:
            with self.subTest(reply):
                self.assertEqual(self.verdict(reply), want)


class FaIssuesTest(unittest.TestCase):
    def test_issues_do_not_accumulate(self):
        bad = "این کتاب ها خوب است"
        first, second = x_review.fa_issues(bad), x_review.fa_issues(bad)
        self.assertEqual(first, second)
        self.assertEqual([i["kind"] for i in first], ["zwnj-ha"])
        self.assertEqual(x_review.fa_issues("متن تمیز"), [])

    def test_latin_digits_in_product_names_filtered(self):
        self.assertEqual(x_review.fa_issues("مدل (Opus 5.5) و GPT-6 آمد"), [])

    def test_real_latin_digits_kept_even_after_a_product_name(self):
        kinds = [i["kind"] for i in x_review.fa_issues("مدل GPT-6 حدود 40 درصد ارزان‌تر است")]
        self.assertEqual(kinds, ["latin-digits"])


class LoopTest(unittest.TestCase):
    def assert_consistent(self, out):
        self.assertEqual(out["check"], x_text.check(out["text"]))
        self.assertEqual(out["history"][out["rounds"]]["text"], out["text"])

    def test_pass_on_round_zero(self):
        out = x_review.write_post(topic(), "en", llm=StubLLM(drafts=[d(EN)], reviews=[PASS]))
        self.assertEqual((out["status"], out["rounds"], out["text"]), ("pass", 0, EN))
        self.assertEqual(out["source_url"], URL_HN)
        self.assertTrue(out["check"]["valid"])
        self.assertEqual(len(out["history"]), 1)

    def test_revise_then_pass_and_feedback_reaches_next_draft(self):
        llm = StubLLM(drafts=[d("Groundbreaking! " + EN), d(EN)], reviews=[REVISE, PASS])
        out = x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual((out["status"], out["rounds"]), ("pass", 1))
        self.assertTrue(any("state the fact" in p and "Groundbreaking! Anthropic" in p for p in llm.prompts))

    def test_gives_up_after_two_revisions(self):
        llm = StubLLM(drafts=[d(EN)] * 3, reviews=[REVISE] * 3)
        out = x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual((out["status"], out["rounds"], len(out["history"])), ("gave_up", 2, 3))
        self.assertEqual(out["history"][-1]["review"]["issues"], REVISE["issues"])
        self.assert_consistent(out)

    def test_rejected_draft_counts_as_a_round(self):
        out = x_review.write_post(topic(), "en", llm=StubLLM(drafts=[d("x", "e9"), d(EN)], reviews=[PASS]))
        self.assertEqual((out["status"], out["rounds"]), ("pass", 1))

    def test_rejected_last_draft_returns_the_last_reviewed_candidate(self):
        # Round-1 finding 9: text/check/rounds must describe the same candidate.
        llm = StubLLM(drafts=[d("First. " + EN), d("Second. " + EN), d("x", "e9")], reviews=[REVISE, REVISE])
        out = x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual((out["status"], out["rounds"], out["text"]), ("gave_up", 1, "Second. " + EN))
        self.assert_consistent(out)
        self.assertIsNone(out["history"][2]["text"])
        self.assertEqual(out["history"][2]["review"]["issues"][0]["rule"], "url")

    def test_exception_in_fa_leaves_en_intact(self):
        llm = StubLLM(drafts=[d(EN)], reviews=[PASS], fail_on="LANGUAGE: fa")
        both = x_review.write_posts(topic(), ["en", "fa"], llm=llm)
        self.assertEqual(both["en"]["status"], "pass")
        self.assertEqual(both["fa"]["status"], "error")
        self.assertIn("stub llm failure", both["fa"]["error"])


class TimeoutTest(unittest.TestCase):
    def test_timeout_and_effort_kwargs_reach_llm_for_draft_and_review(self):
        llm = StubLLM(drafts=[d(EN)], reviews=[PASS])
        x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual(llm.calls, ["draft", "review"])
        self.assertEqual(llm.kwargs, [{"timeout": 180, "effort": "medium"}] * 2)
        self.assertEqual((x_review.LLM_TIMEOUT, x_review.LLM_EFFORT), (180, "medium"))

    def test_retry_keeps_effort(self):
        llm = StubLLM(drafts=[d(EN)], reviews=[PASS])
        llm.timeouts["review"] = 1
        x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual(llm.kwargs[-2:], [{"timeout": 180, "effort": "medium"}] * 2)


class ClaudeJsonEffortTest(unittest.TestCase):
    def argv(self, **kw):
        out = SimpleNamespace(stdout=json.dumps({"structured_output": {"ok": 1}}), returncode=0, stderr="")
        with mock.patch.object(rank.subprocess, "run", return_value=out) as run:
            self.assertEqual(rank.claude_json("p", {}, **kw), {"ok": 1})
        return run.call_args.args[0]

    def test_effort_is_opt_in_and_default_argv_unchanged(self):
        default = self.argv()
        self.assertNotIn("--effort", default)
        self.assertEqual(default[-2:], ["--json-schema", "{}"])
        medium = self.argv(effort="medium")
        self.assertEqual(medium, default + ["--effort", "medium"])

    def test_one_timeout_is_retried_once(self):
        for kind in ("draft", "review"):
            with self.subTest(kind):
                llm = StubLLM(drafts=[d(EN)], reviews=[PASS])
                llm.timeouts[kind] = 1
                out = x_review.write_post(topic(), "en", llm=llm)
                self.assertEqual(out["status"], "pass")
                self.assertEqual(llm.calls.count(kind), 2)

    def test_repeated_timeout_is_an_error_after_two_calls_other_language_unaffected(self):
        for kind in ("draft", "review"):
            with self.subTest(kind):
                llm = StubLLM(drafts=[d(FA), d(EN)], reviews=[PASS, PASS])
                llm.timeouts[kind] = -1
                fa = x_review.write_post(topic(), "fa", llm=llm)
                self.assertEqual(fa["status"], "error")
                self.assertIn("TimeoutExpired", fa["error"])
                self.assertEqual(llm.calls.count(kind), 2)
                llm.timeouts[kind] = 0
                llm.drafts = [d(EN)]
                self.assertEqual(x_review.write_post(topic(), "en", llm=llm)["status"], "pass")

    def test_other_exceptions_are_not_retried(self):
        llm = StubLLM(drafts=[d(EN)], fail_on="LANGUAGE: en")
        out = x_review.write_post(topic(), "en", llm=llm)
        self.assertEqual((out["status"], llm.calls), ("error", ["draft"]))


INVALID = [  # (lang, draft) pairs that a deterministic gate must stop even with an always-pass reviewer
    ("en", d("a" * 260)),                         # fits before, overflows after the URL is appended (285)
    ("en", d(f"Visit evil.com {URL_HN}")),
    ("en", d(f"Visit HTTPS://evil.com/x {URL_HN}")),
    ("en", d(f"Two links {URL_HN} {URL_HN}")),
    ("fa", d(f"Claude منتشر شد. {URL_HN}")),
    ("fa", d(f"\u200fClaude منتشر شد. {URL_HN}")),
    ("fa", d(f"\u061cClaude منتشر شد. {URL_HN}")),
    ("fa", d(f"آنتروپیک — مدل تازه. {URL_HN}")),
    ("fa", d(f"آنتروپیک – مدل تازه. {URL_HN}")),
]


class LoopGateIntegrationTest(unittest.TestCase):
    """Round-1 finding 3: the gates must hold inside write_post, not only when review() is called directly."""

    def test_invalid_round_zero_never_reaches_the_reviewer(self):
        for lang, bad in INVALID:
            good = EN if lang == "en" else FA
            with self.subTest(lang=lang, text=bad["text"][:40]):
                llm = StubLLM(drafts=[bad, d(good)], reviews=[PASS])
                out = x_review.write_post(topic(), lang, llm=llm)
                self.assertEqual((out["status"], out["rounds"], out["text"]), ("pass", 1, good))
                self.assertEqual(out["check"], x_text.check(good))
                self.assertEqual(llm.calls.count("review"), 1)
                self.assertTrue(out["history"][0]["review"]["gated"])

    def test_invalid_last_revision_gives_up_not_pass(self):
        for lang, bad in INVALID:
            good = EN if lang == "en" else FA
            with self.subTest(lang=lang, text=bad["text"][:40]):
                llm = StubLLM(drafts=[d(good), d(good), bad], reviews=[REVISE, REVISE, PASS])
                out = x_review.write_post(topic(), lang, llm=llm)
                self.assertEqual((out["status"], out["rounds"]), ("gave_up", 2))
                self.assertEqual(out["check"], x_text.check(out["text"]))
                self.assertTrue(out["history"][2]["review"]["gated"])
                self.assertEqual(llm.calls.count("review"), 2)


class CliTest(unittest.TestCase):
    def research(self, tmp, topics):
        path = Path(tmp) / "research.json"
        path.write_text(json.dumps({"schema": "x-research/1", "date": "2026-09-24", "topics": topics}),
                        encoding="utf-8")
        return path

    def test_topic_by_index_and_id_select_same_topic_and_write_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            research = self.research(tmp, [{**topic(), "id": "other"}, topic()])
            runs = Path(tmp) / "runs"
            for sel in ("2", topic()["id"]):
                llm = StubLLM(drafts=[d(EN)], reviews=[PASS])
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = x_cli.main(["draft", "--research", str(research), "--topic", sel, "--lang", "en",
                                     "--runs", str(runs)], llm=llm)
                self.assertEqual(rc, 0)
                self.assertIn("Opus 5.5 lands", llm.prompts[0])
            out = runs / "2026-09-24" / topic()["id"] / "post_en.json"
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "pass")

    def test_unknown_topic_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            research = self.research(tmp, [topic()])
            with self.assertRaises(SystemExit):
                x_cli.main(["draft", "--research", str(research), "--topic", "9"], llm=StubLLM())

    def test_lang_both_survives_unencodable_en_output(self):
        # Round-1 finding 7: a lone surrogate in EN crashed printing on a strict UTF-8 console before FA ran.
        with tempfile.TemporaryDirectory() as tmp:
            research, runs = self.research(tmp, [topic()]), Path(tmp) / "runs"
            llm = StubLLM(drafts=[d("News \ud800")] * 3 + [d(FA)], reviews=[PASS])
            console = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="strict")
            with contextlib.redirect_stdout(console):
                rc = x_cli.main(["draft", "--research", str(research), "--topic", "1", "--lang", "both",
                                 "--runs", str(runs)], llm=llm)
            self.assertEqual(rc, 0)
            base = runs / "2026-09-24" / topic()["id"]
            self.assertEqual(json.loads((base / "post_en.json").read_text(encoding="utf-8"))["status"], "gave_up")
            self.assertEqual(json.loads((base / "post_fa.json").read_text(encoding="utf-8"))["status"], "pass")


if __name__ == "__main__":
    unittest.main()
