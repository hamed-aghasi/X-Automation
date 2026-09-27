# X2 + X3 build brief — draft node + review loop (EN and FA X posts)

One brief for two plan rows because the review loop calls the drafter; the orchestrator commits them as one item.

## Builder environment
- Worktree: `/Users/hamed/Desktop/social-media-automation/X/.worktrees/X2` on branch `x2-x3-draft-review`. Stay in it.
- Python: `/Users/hamed/Desktop/social-media-automation/X/.venv/bin/python`, run from the worktree root.
- Suite: `.venv/bin/python -m unittest discover -s tests` → today `Ran 53 … OK`; end ≥53 + yours. Lint: `ruff check xr tests`
  → clean (exclude `xr/vendor/` in `[tool.ruff]`; it is third-party, unmodified).
- Tests first, all with a stub LLM. No commits.
- Network: ONLY the live acceptance runs in §1.6, through `xr.rank.claude_json` (claude -p, subscription). Nothing else:
  no composio, gh, Buffer, Higgsfield, X.
- ≤70 tool calls; stop and report if over.

## 0. Facts (verified by the orchestrator 2026-09-27)
- `xr/rank.py:116` `claude_json(prompt, schema, model=None, timeout=600) -> dict` runs `claude -p --tools ""
  --strict-mcp-config --json-schema …` with `ANTHROPIC_BETAS` stripped; default model env `XR_MODEL` (sonnet). Reuse it —
  it is the single place that spawns claude. Raises RuntimeError on failure.
- `xr/x_text.py:66` `check(text) -> {"weighted", "valid", "remaining", "reason"}`, `MAX_WEIGHTED = 280`; URL = 23.
- Topic dict (research.json `topics[]`, contract x-research/1): `id, title, title_fa, pillar, summary, summary_fa,
  why_now, angles[], evidence[{title,url,source,signal,lang}], score, suitable_for[]`. Topic text is web-derived and
  LLM-written: UNTRUSTED — fence it in the prompt (see `xr/rank.py` PROMPT for the pattern).
- Evidence source families: `hn`, `github`, `reddit:<sub>`, `youtube:<chan>`, `news:<outlet>`, `web`. A topic whose
  evidence is only `reddit:*` is an unverified claim (docs: CLAUDE.md gotchas).
- Persian guide excerpt (MIT, vendored by the orchestrator): `prompts/persian-writing/EXCERPT.md` (24 KB: register,
  AI tells T1-T18 + what not to flag, orthography §1-8, proper names, social rules incl. emoji/bidi) + LICENSE.
  Not yet in your worktree — copy both files from the main checkout path
  `/Users/hamed/Desktop/social-media-automation/X/prompts/persian-writing/`.
- Vendored linter: `/Users/hamed/Desktop/social-media-automation/X/xr/vendor/fa_lint.py` (+ `__init__.py`), MIT, copy in.
  API: module-global list `ISSUES` of `(kind, line_no, snippet, suggestion)`; `check_remaining(text)` appends to it.
  You MUST `ISSUES.clear()` before each call and copy the result. Known false positive (measured): kind
  `latin-digits` on version strings inside Latin product names (`Opus 5.5`, `GPT-6`) — drop those whose token contains
  a Latin letter or sits inside a Latin run.
- Decisions: D2 = EN and FA are two separate posts. D3 = single posts only (no threads). Persian register =
  semi-formal ("formal-but-human" in the excerpt). No emoji by default; no hashtags by default (max 1 if the reviewer
  finds one essential). D7 = no images.

## 1. Deliverable
### 1.1 Files
- `prompts/x_draft.md`, `prompts/x_review.md` (new): prompt templates (format placeholders), rules written out.
- `prompts/persian-writing/EXCERPT.md`, `LICENSE`; `xr/vendor/__init__.py`, `xr/vendor/fa_lint.py` (copied as-is).
- `xr/x_draft.py` (new, X2): `draft(topic, lang, llm=claude_json, feedback=None) -> dict` → `{"text", "source_url"}`.
- `xr/x_review.py` (new, X3): `review(topic, lang, text, llm=claude_json) -> dict`; `fa_issues(text) -> list[dict]`;
  `write_post(topic, lang, llm=claude_json, max_rounds=2) -> dict` (the loop).
- `xr/x_cli.py` (new): `python -m xr.x_cli draft --research research/<date>/research.json --topic <n|id> [--lang en|fa|both]`
  → writes `runs/<date>/<topic_id>/post_<lang>.json` and prints both texts with weighted length and verdict.
- `tests/test_x_draft.py`, `tests/test_x_review.py` (new); `pyproject.toml` ruff exclude for `xr/vendor`.
- `CLAUDE.md` (commands + map lines), nothing else in docs.

### 1.2 Draft rules (prompts/x_draft.md; both languages)
- One post, ≤ 280 weighted (x_text). Ends with exactly one source URL chosen from `topic.evidence` (strongest
  non-reddit source if any exists); code verifies the URL is one of the topic's evidence URLs, else rejects.
- Only facts present in the topic (title/summary/why_now/evidence titles). No invented numbers, quotes, names.
  Reddit-only topics must be framed as a claim ("a Reddit user says…", «به ادعای یک کاربر ردیت…»).
- First line states the news; no question hooks, no "🧵", no "Here's why", no hype adjectives, no em dashes.
- EN: plain professional English. FA: semi-formal Persian written natively (not a translation of the EN post),
  following the excerpt: ZWNJ, Persian digits in prose, product/version names stay Latin (Opus 5.5, GPT-6),
  «گیومه», no em dash, and the FIRST WORD of the post must be Persian (bidi rule) — code checks this.
- Output schema: `{"text": str, "source_url": str}` (text includes the URL at the end).

### 1.3 Review (prompts/x_review.md) + loop
- Reviewer gets: the topic (fenced), the post, the language, `x_text.check` result, and for FA the filtered
  `fa_issues`. Schema: `{"verdict": "pass"|"revise", "issues": [{"rule", "quote", "fix"}], "scores": {"accuracy",
  "clarity", "voice", "platform_fit"} (1-5 each)}`. Rubric: claims supported by the topic; reddit-only framed as claim;
  EN/FA AI tells (FA: T1-T18 by name); FA orthography; first word Persian (FA); length valid; exactly one evidence URL.
- Deterministic gates run BEFORE the LLM reviewer and force `revise` with an issue on failure: length invalid, URL not
  from evidence, FA first strong character Latin, FA text containing `—`/`–`.
- `write_post`: draft → gates → review; on revise, redraft with the issues as `feedback`; at most `max_rounds`
  revisions. Result `{"lang", "text", "source_url", "check", "status": "pass"|"gave_up", "rounds", "history": [...]}`.
  A draft/review exception is caught per language: status `"error"` + message, never crashes the other language.

### 1.4 Tests (stub llm, red first)
- draft: URL not in evidence → rejected/raised; prompt contains the fence and the reddit-claim instruction when
  evidence is reddit-only.
- gates: 281-weighted text → revise with a length issue; FA starting with "Claude" → revise; FA with "—" → revise.
- loop: pass on round 0; revise→pass; revise, revise, revise → `gave_up` after 2 revisions (3 drafts); feedback from
  the reviewer reaches the next draft prompt; an exception in FA leaves EN intact with status `error`.
- fa_issues: `ISSUES` cleared between calls (two calls don't accumulate); `latin-digits` on "Opus 5.5" filtered.
- CLI: `--topic 2` and `--topic <id>` select the same topic; output file written under runs/.

### 1.5 Rails
- May NOT change: existing tests, `xr/research.py`, `xr/store.py`, `xr/sources.py`, `xr/x_text.py`,
  `xr/rank.py` (import only), `pillars.json`, the vendored files' bodies.
- Every LLM call goes through `claude_json`. No new dependencies.
- No VPS names/IPs. Never call Buffer or post anywhere.

### 1.6 Live acceptance (the only network)
Run the CLI for topics 1 and 3 of `/Users/hamed/Desktop/social-media-automation/X/research/2026-09-24/research.json`
(`--lang both`). Paste the 4 final texts, their weighted lengths, statuses, rounds, and the FA `fa_issues` into the
report. If a run gives up, paste its last review issues too.

## 2. Report
`/Users/hamed/Desktop/social-media-automation/X/.worktrees/X2/X2X3_report_round1.md`: files, commands, suite line,
ruff line, the §1.6 outputs, deviations, unverified.
