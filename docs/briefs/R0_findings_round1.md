# R0 findings — round 1 triage (2026-09-26)

Reviewer: Codex CLI gpt-6-astra, read-only (`R0_review_round1.md`). Triage by the orchestrator; evidence re-run.

| # | Sev | Verdict | Evidence (orchestrator) | Fix scope |
|---|---|---|---|---|
| 1 | blocker | REAL | `claude -p --tools ""` answered with `mcp__blender__execute_blender_code …` (Mac, 2026-09-26); with `--strict-mcp-config` added, no MCP tools. Prompt carries untrusted web text; VPS has Higgsfield MCP authed. Whether a call would pass permissions is unproven; exposure alone is the defect. | add `--strict-mcp-config` to `rank.claude_json`; strip `ANTHROPIC_BETAS` from the child env; test the argv |
| 2 | minor | REAL | slug truncated to 60 chars (`xr/rank.py:91`); `INSERT OR REPLACE` (`xr/store.py:86`) overwrites. Rare but silent. | id = `<date>-<slug>-<6 hex of sha1(sorted evidence urls)>` |
| 3 | major | REAL, scoped | Same story on day 2 gets a new id → `unused_topics("x")` offers it again → X could post a story twice. Full event identity is out of scope. | `unused_topics(platform)` excludes topics sharing any evidence URL with a topic already used on that platform |
| 4 | major | REAL | `urlsplit("http://[bad")` → `ValueError: Invalid IPv6 URL` (re-run); `normalize` has no handler. | per-item guard in `Store.fresh`; bad items dropped and reported in `errors` |
| 5 | major | REAL | `run_composio`/`run_trends` ignore returncode and `zip` truncates (`xr/sources.py:163-170,189-196`). | validate envelope; one error per call with no result; keep per-call successes when exit ≠ 0 |
| 6 | minor | REAL | `_follow_spill` swallows `OSError` → pointer dict parsed as empty data, no error. | record a per-call error for unreadable/undecodable spill files |
| 7 | major | REAL | `hacker_news`/`github` loop has no per-query guard; one failed query zeroes the source. | per-query try; return items + attributed errors (fetcher contract already `(items, errors)`) |
| 8 | major | REAL | `write` overwrites `research.json` even when `rank` failed → a same-day rerun can replace good topics with `[]`. | atomic writes (tmp + `os.replace`); when rank errored and the day's existing file has topics, keep it and write `research.failed.json` instead |
| 9 | minor | REAL | fixture last bucket `Sep 20–26, 2026` has `partial_data: true`. | drop partial trailing buckets before computing momentum; assert the fixture value |
| 10 | minor | REAL | batch test never calls `run_composio`; no argv test for `claude_json`. | covered by tests for 1, 5, 6 |
| — | — | DISMISSED, review-input | reviewer's sandbox blocked temp files for 2 graph tests; the orchestrator's run: 15/15 green | none |

Plus the row's lint gate: `pyproject.toml` pins ruff (target py313, line-length 120, default rule set kept);
`ruff check xr tests` 8 → 0.

## Re-check (filled after the fix round)
| # | Re-checked by | Result |
|---|---|---|
| 1 | Codex (R0_recheck_round1.md) + orchestrator live run | FIXED. Codex "PARTIAL: StructuredOutput remains" → DISMISSED by design (that tool is how --json-schema returns output; read-only). MCP isolation measured live 2026-09-26: without the flag MCP tools listed, with it none. |
| 2, 3, 6, 9, 10 | Codex | FIXED |
| 4 | Codex | PARTIAL → REAL minor: mixed str/float signal raises outside the guard (unreachable from our parsers, cheap) → round 2 |
| 5 | Codex | PARTIAL: malformed `data` in one result aborts the batch → REAL, round 2. "successful with no data → no items, no error" → DISMISSED (a legitimate empty result). Timeout = one error for the batch → DOWNGRADED (correct: the batch did fail). |
| 7 | Codex | PARTIAL → REAL: parsing (`{"hits": null}`) is outside the per-query guard → round 2 |
| 8 | Codex | FIXED; atomicity untested → DOWNGRADED (test gap, not a defect) |
| N1 | Codex, new | REAL major: failed same-day rerun keeps old files but drops the newly collected items → round 2 (write `items.failed.json`) |
| N2 | Codex, new | REAL major: narrowed catch in the rank node lets `AttributeError` skip `write` (reproduced by Codex) → restore broad catch with `# noqa: BLE001` + reason → round 2 |
| N3 | Codex, new | REAL minor: shared `.tmp` name across concurrent writers → unique temp file in the same dir → round 2 |
| N4 | Codex, new | REAL minor: ruff version not pinned → `[dependency-groups] dev` pin → round 2 |
