# X2+X3 findings — round 1 triage (2026-09-27)

Reviewer: Codex gpt-6-astra read-only (`X2X3_review_round1.md`). Orchestrator own run: 78 tests OK, ruff clean.
Fact-check of the 4 live posts against research/2026-09-24 topics 1 and 3: every number, name and URL is present in the
topic (680k lines, $20 Pro, Team Standard, 40%, Fable 5.1, 15,465, China/Russia/home networks, hardcoded, authorization).
One scope error: topic 3 EN "15,465 public MCP servers send credentials…" vs topic "analysis of 15,465 servers found…",
passed with accuracy 5. Threat model: topic text is untrusted (web-derived, LLM-written) and may try to steer either LLM.

| # | Sev | Verdict | Fix scope |
|---|---|---|---|
| 1+8 | high | REAL | URL gate: extract URLs with twitter-text (the library x_text already wraps) — bare domains, any case; require exactly ONE URL, at the end, equal to the returned `source_url`, which must be an evidence URL (exact match) |
| 2 | high | REAL (measured live) | x_review.md accuracy rule: each number keeps its role (sample/studied vs affected), quantifiers and hedges preserved; broader scope → blocking issue; include this exact negative example + the correct "An analysis of 15,465 servers found…" form; same line in x_draft.md |
| 3 | high | REAL | integration tests of write_post with an always-pass reviewer and invalid drafts at round 0 AND the last revision (overflow after URL append, extra/bare-domain URL, FA Latin opening incl. RLM/ALM prefix, both dashes); assert status, final text/check consistency, reviewer call counts |
| 4 | med | REAL | FA opening gate: skip Cf/format chars and whitespace/punctuation; first LETTER must be Arabic-script (U+0600-06FF / FB50-FDFF / FE70-FEFF); a leading digit fails |
| 5 | med | REAL | evidence offered to the model as fenced JSON with ids (e0, e1 …); model returns `source_id`; code resolves the URL. No raw evidence field outside the fence |
| 6 | med | REAL | review schema issues gain `severity: blocking|minor`; code forces revise if any blocking issue or accuracy < 4 or any score < 3 |
| 7 | med→low | REAL | CLI: per-language serialization/printing inside the isolation boundary; ensure_ascii for console-unsafe text; `--lang both` regression test |
| 9 | low | REAL | returned text/check/rounds describe the same candidate; rejected-candidate diagnostics stay in history |
| 10 | — | VERIFIED by reviewer | core length/dash gates hold at the final revision; loop bounded |
