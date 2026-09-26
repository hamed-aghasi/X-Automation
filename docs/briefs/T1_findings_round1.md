# T1 findings — round 1 triage (2026-09-26)

Reviewer: Codex gpt-6-astra read-only (`T1_review_round1.md`). Orchestrator own run first: 57 tests OK, pyflakes clean;
real VPS research.json 2026-09-25 renders /topics 1,348 chars, /topic 1 2,318 chars, `&` escaped, 9 RLM lines.
Threat model: research.json is written by our own pipeline (same host, same uid); only the STRINGS inside are
untrusted (web titles, LLM summaries). The directory/file structure is not attacker-controlled.

| # | Sev | Verdict | Reasoning | Fix scope |
|---|---|---|---|---|
| 1 | major | REAL | emoji-heavy strings: 3,838 source chars → 7,370 UTF-16 units; Telegram rejects → no reply | budget every reply in UTF-16 units of the HTML source (≥ parsed length → safe); astral-char tests |
| 7 | major→minor | REAL (cheap) | quadratic evidence truncation; real lists are ≤~8 | fold into #1: build once with a running budget; cap evidence at 20, angles at 10 |
| 8 | minor | REAL | fallback slices raw HTML inside an entity | fold into #1: truncate decoded text before escaping; never slice HTML |
| 2 | major→minor | REAL | huge `date` field / 4,089-digit arg overflow | header date = the validated folder name; `/topic` arg: 1-3 ASCII digits else usage |
| 3 | major→minor | REAL | `/topic ²` → ValueError (`isdigit`) | ASCII-only `[0-9]{1,3}` |
| 4 | major→minor | REAL | `https://[` URL → ValueError; `"evidence": 1` → TypeError | tolerate: bad URL → escaped text; non-list fields → skipped; lone surrogates → replaced |
| 5 | major→minor | REAL | PermissionError from iterdir escapes | catch OSError around the whole scan → "No research available yet." |
| 6 | major | DISMISSED (threat model) | only our own process writes the dir; planting a symlink/FIFO needs the host already | none (read-only mount stays) |
| 9 | minor | DOWNGRADED | allow-list check is pre-existing code T1 did not touch; test gap logged for a later bot item | none in T1 |
