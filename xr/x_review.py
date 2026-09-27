"""X3: review an X post (deterministic gates, then a Claude editor) and the draft -> review -> redraft loop."""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata

from xr import x_text
from xr.rank import claude_json
from xr.vendor import fa_lint
from xr.x_draft import PROMPTS, DraftRejected, draft, evidence_urls, fence, persian_guide, reddit_only, topic_view

LATIN = re.compile(r"[A-Za-z]")

SCHEMA = {
    "type": "object",
    "required": ["issues", "scores"],
    "properties": {
        "issues": {"type": "array", "items": {
            "type": "object", "required": ["rule", "severity", "quote", "fix"],
            "properties": {"rule": {"type": "string"}, "severity": {"enum": ["blocking", "minor"]},
                           "quote": {"type": "string"}, "fix": {"type": "string"}}}},
        "scores": {"type": "object", "required": ["accuracy", "clarity", "voice", "platform_fit"],
                   "properties": {k: {"type": "integer", "minimum": 1, "maximum": 5}
                                  for k in ("accuracy", "clarity", "voice", "platform_fit")}},
    },
}


LLM_TIMEOUT = 180  # s per draft/review call; claude -p stalls intermittently (measured: 600 s stalls vs ~50 s normal)
# Measured 2026-09-27 (sonnet): default effort 53->150+ s and erratic; low 9-15 s but caught the scope error 1/3;
# medium 11-14 s and caught it 3/3 (clean FA review 20-101 s).
LLM_EFFORT = "medium"


def call_llm(llm, prompt: str, schema: dict) -> dict:
    """One draft/review LLM call at LLM_EFFORT with a per-call timeout, retried once on TimeoutExpired only."""
    try:
        return llm(prompt, schema, timeout=LLM_TIMEOUT, effort=LLM_EFFORT)
    except subprocess.TimeoutExpired:
        return llm(prompt, schema, timeout=LLM_TIMEOUT, effort=LLM_EFFORT)


SCORE_KEYS = ("accuracy", "clarity", "voice", "platform_fit")
ARABIC_SCRIPT = ((0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))


def opens_persian(text: str) -> bool:
    """The first visible LETTER is Arabic-script. Format controls (RLM U+200F, ALM U+061C, ZWNJ ...), whitespace,
    punctuation, symbols and marks are skipped, since a direction mark does not make a Latin word Persian;
    a digit before any letter fails (the post must open with a word)."""
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] == "N":
            return False
        if cat[0] == "L":
            return any(lo <= ord(ch) <= hi for lo, hi in ARABIC_SCRIPT)
    return False


def _latin_run(tokens: list[str], n: int) -> bool:
    """Digits inside a Latin product name (GPT-6, Opus 5.5) stay Latin by the local rule."""
    if LATIN.search(tokens[n]):
        return True
    prev = tokens[n - 1].strip("()[]«»\"',،؛:") if n else ""
    return bool(prev) and bool(LATIN.match(prev[-1]))


def _latin_digits(line_no: int, line: str) -> dict | None:
    tokens = line.split()
    for n, tok in enumerate(tokens):
        if re.search(r"[0-9]", tok) and not fa_lint._skip_token(tok) and not _latin_run(tokens, n):
            return {"kind": "latin-digits", "line": line_no, "snippet": line.strip()[:80],
                    "suggestion": f"{tok}: Persian digits in Persian prose"}
    return None


def fa_issues(text: str) -> list[dict]:
    """fa_lint.check_remaining with its module-global ISSUES isolated per call. The linter reports only the first
    Latin-digit token per line, and that is often a product version (a measured false positive), so `latin-digits`
    is recomputed here with the Latin-run filter instead of trusting the linter's single hit."""
    fa_lint.ISSUES.clear()
    try:
        fa_lint.check_remaining(text)
        raw = list(fa_lint.ISSUES)
    finally:
        fa_lint.ISSUES.clear()
    out = [{"kind": k, "line": ln, "snippet": s, "suggestion": sug} for k, ln, s, sug in raw if k != "latin-digits"]
    for ln, line in enumerate(text.split("\n"), 1):
        if re.search(fa_lint.FA_LETTER, line) and (hit := _latin_digits(ln, line)):
            out.append(hit)
    return out


def gates(topic: dict, lang: str, text: str, source_url: str | None = None) -> list[dict]:
    """URLs are found with X's own extractor (bare domains, any case). Exactly one, at the end, an evidence URL
    (exact match) and, when given, equal to the draft's source_url."""
    issues = []
    chk = x_text.check(text)
    if not chk["valid"]:
        issues.append({"rule": "length", "quote": f"weighted {chk['weighted']} ({chk['reason']})",
                       "fix": f"cut to at most {x_text.MAX_WEIGHTED} weighted characters (URL counts 23)"})
    urls, allowed = x_text.extract_urls(text), set(evidence_urls(topic))
    if (len(urls) != 1 or urls[0] not in allowed or not text.rstrip().endswith(urls[0])
            or (source_url is not None and urls[0] != source_url)):
        issues.append({"rule": "url", "quote": " ".join(urls) or "(no URL)",
                       "fix": "end with exactly one URL copied from the topic's evidence, and no other URL"})
    if lang == "fa":
        if not opens_persian(text):
            issues.append({"rule": "first-word", "quote": text.split()[0] if text.split() else "",
                           "fix": "start the post with a Persian word (bidi rule); move the Latin name later"})
        for ch in ("—", "–"):
            if ch in text:
                issues.append({"rule": "dash", "quote": ch, "fix": "no em/en dash in Persian: use ، or ؛ or rephrase"})
    return issues


def build_prompt(topic: dict, lang: str, text: str, chk: dict, fa: list[dict]) -> str:
    rule = ("every source is Reddit, so the post MUST frame the news as a claim (\"A Reddit user says\" / «به ادعای "
            "یک کاربر ردیت»), never as fact." if reddit_only(topic)
            else "not applicable (the topic has non-Reddit sources).")
    return (PROMPTS / "x_review.md").read_text(encoding="utf-8").format(
        lang=lang, topic=fence(topic_view(topic)), post=text.replace("</post>", "<\\/post>"), check=json.dumps(chk),
        fa_issues=fence(fa) if lang == "fa" else "(not applicable)", reddit_rule=rule,
        persian_guide=persian_guide() if lang == "fa" else "")


def decide(issues: list[dict], scores: dict) -> str:
    """Code, not the model, decides: any blocking issue, accuracy < 4 or any score < 3 (missing = 0) -> revise."""
    sc = {k: scores.get(k, 0) if isinstance(scores.get(k), int) else 0 for k in SCORE_KEYS}
    if any(i.get("severity") != "minor" for i in issues) or sc["accuracy"] < 4 or min(sc.values()) < 3:
        return "revise"
    return "pass"


def review(topic: dict, lang: str, text: str, llm=claude_json, source_url: str | None = None) -> dict:
    """Gates first: a failed gate returns "revise" without spending an LLM call."""
    chk = x_text.check(text)
    fa = fa_issues(text) if lang == "fa" else []
    failed = gates(topic, lang, text, source_url)
    if failed:
        failed = [{**i, "severity": "blocking"} for i in failed]
        return {"verdict": "revise", "issues": failed, "scores": {}, "gated": True, "check": chk, "fa_issues": fa}
    out = call_llm(llm, build_prompt(topic, lang, text, chk, fa), SCHEMA)
    issues, scores = list(out.get("issues", [])), dict(out.get("scores", {}))
    return {"verdict": decide(issues, scores), "issues": issues, "scores": scores,
            "gated": False, "check": chk, "fa_issues": fa}


def write_post(topic: dict, lang: str, llm=claude_json, max_rounds: int = 2) -> dict:
    """draft -> review; on revise, redraft with the issues, at most `max_rounds` revisions (max_rounds+1 drafts).
    text/source_url/check/rounds always describe ONE candidate: the last draft that was reviewed (`rounds` is its
    round); rejected drafts (unknown source_id) live only in `history`. Never raises: an LLM/runtime failure
    returns status "error" with the history so far. Only status "pass" means approved."""
    history, feedback = [], None

    def timed(prompt, schema, **_):  # draft calls get the same timeout + single retry as review calls
        return call_llm(llm, prompt, schema)
    cand = {"text": None, "source_url": None, "check": None, "rounds": 0}

    def result(status: str, **extra) -> dict:
        return {"lang": lang, **cand, "status": status, **extra, "history": history}

    try:
        for rnd in range(max_rounds + 1):
            try:
                d = draft(topic, lang, llm=timed, feedback=feedback)
            except DraftRejected as exc:
                issues = [{"rule": "url", "severity": "blocking", "quote": str(exc),
                           "fix": "return source_id as one of the evidence ids (e0, e1 ...)"}]
                history.append({"round": rnd, "text": None, "review": {"verdict": "revise", "issues": issues}})
                feedback = {"previous_text": None, "issues": issues}
                continue
            rv = review(topic, lang, d["text"], llm=llm, source_url=d["source_url"])
            cand = {**d, "check": rv["check"], "rounds": rnd}
            history.append({"round": rnd, "text": d["text"], "source_url": d["source_url"], "review": rv})
            if rv["verdict"] == "pass":
                return result("pass")
            feedback = {"previous_text": d["text"], "issues": rv["issues"]}
        return result("gave_up")
    except Exception as exc:  # noqa: BLE001 - one language failing must not take down the other
        return result("error", error=f"{type(exc).__name__}: {exc}")


def write_posts(topic: dict, langs, llm=claude_json, max_rounds: int = 2) -> dict:
    return {lang: write_post(topic, lang, llm=llm, max_rounds=max_rounds) for lang in langs}
