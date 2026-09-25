# R0 review brief — adversarial review of the research graph (bb6676e)

## Reviewer environment
- Seat: Codex CLI, `-s read-only`, repo root = working dir. Different model family from the author (Claude).
- You may read any file and run read-only commands (`.venv/bin/python -m unittest discover -s tests`,
  `ruff check xr tests`, `git log`, `grep`). Do NOT call the network, `composio`, `gh`, or `claude`.
- Verify, do not trust: the author's docs (CLAUDE.md, docs/PLAN.md, docstrings) are claims.

## 0. Facts (orchestrator survey, 2026-09-26)
- Code under review: `xr/sources.py` (198 lines), `xr/store.py` (100), `xr/rank.py` (123), `xr/research.py` (166);
  tests `tests/test_research.py` (167, 15 tests, green). Fixtures in `tests/fixtures/` are real Composio output.
- Graph: `xr/research.py:build_graph` — fetch_* nodes + `trends` fan out from START, fan in to `normalize`
  (`add_edge([...], "normalize")`), then `rank` → `write`. Reducers: `items`/`errors` `operator.add`,
  `source_counts` `operator.or_` (`xr/research.py:30-32`).
- Subprocess calls: `xr/rank.py:110` (`claude -p`), `xr/sources.py:83` (`gh api`), `:163` and `:189` (`composio`).
- Runtime: runs daily-ish on a Linux VPS as an unprivileged user whose `~/.claude.json` has an authenticated
  Higgsfield MCP server (paid image generation) configured. Also runs on a Mac.
- `ruff check xr tests` baseline: 8 findings (PLW1510 ×3, BLE001 ×3, UP035, ISC004). Not your job to list those.
- Output contract: `research/<date>/research.json` with `"schema": "x-research/1"`, consumed by other platforms.

## 1. What to review
Hunt for defects that matter, across: correctness, security (untrusted web content reaches an LLM), data integrity
of `data/research.db` across repeated runs, error handling / silent data loss, LangGraph state semantics, and
test weakness (tests that would still pass if the code were wrong).

Claims the author makes that you must verify or refute, each with file:line evidence:
1. Untrusted item text cannot make the ranking LLM call take any action (no built-in tools, no MCP tools).
2. A topic's evidence can only point at items that were actually collected (no invented URLs).
3. One failing source never kills the run; its failure is recorded in `errors`.
4. Re-running on the same day does not duplicate or corrupt items, topics, or usage rows.
5. `Store.fresh` drops items published >7 days ago and items first seen more than `hours` ago; undated items kept.
6. Composio batch results are attributed to the right (slug, pillar, lang) call.
7. Topic ids are unique and stable enough for `usage` (per-platform "already used") to be correct.

## 2. Output
Write ONLY this, as markdown, to your final message:
- A table: `# | severity (blocker/major/minor/nit) | file:line | claim | evidence (quote or reasoning) | suggested fix`.
- Then one line per numbered claim above: VERIFIED / REFUTED / UNCLEAR + the file:line that decides it.
- No praise, no summary of what the code does. If you are not sure a finding is real, say so in the evidence column.
