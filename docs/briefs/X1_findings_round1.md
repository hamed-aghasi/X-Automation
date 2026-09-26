# X1 findings — round 1 triage (2026-09-26)

Reviewer: Codex gpt-6-astra read-only (`X1_review_round1.md`). Orchestrator own run first: 49 tests OK, ruff clean,
fresh `python -I` import works and leaves no `pkg_resources` behind; library uses pkg_resources only at
`twitter_text/regexp/emoji.py:108` (`resource_string` of the bundled emoji-test.txt).

| # | Sev | Verdict | Evidence / reasoning | Fix scope |
|---|---|---|---|---|
| 1 | major | REAL | library collapses CRLF → LF; `"س"*279+"\r\n"` → 280 valid (NFC-only v3 gives 281). Wrong in the UNSAFE direction (can pass an over-length post). | count conservatively: add one per `\r\n`; boundary test on both functions |
| 2 | major→minor | REAL, downgraded | leak needs a concurrent `import pkg_resources` in another thread during our import; nothing in the pipeline does that. Still worth removing the shim if a declared dependency can do it. | try a `setuptools` pin that ships `pkg_resources` on py3.13 (measure: fresh venv import works, no warning spam); if it works, delete the shim; if not, keep the shim and say why |
| 3 | major→minor | DOWNGRADED | bundled emoji data is Emoji 12.0 (2019-01-27); newer sequences overcount (`🧑‍💻` = 5). Error is in the SAFE direction (never over-posts). X's live count for new emoji is not verifiable offline. Drafts default to no emoji (persian-writing guide). | no code change; state the limit in the x_text docstring and CLAUDE.md gotchas |
| 4 | minor | REAL | lone surrogate `"\ud800"` raises UnicodeEncodeError in both functions; json can yield it. | `check()` → reason `invalid_char`; `weighted_length()` defined behaviour (raise ValueError); tests |
