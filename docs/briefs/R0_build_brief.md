# R0 build brief — fix the 10 REAL review findings + wire lint

## Builder environment
- Worktree: `/Users/hamed/Desktop/social-media-automation/X/.worktrees/R0` on branch `r0-review-fixes`. Do not leave it.
- Python: `/Users/hamed/Desktop/social-media-automation/X/.venv/bin/python` (run from the worktree root so `xr` imports
  from the worktree). Lint: `ruff check xr tests`.
- Suite: `.venv/bin/python -m unittest discover -s tests` → today `Ran 15 … OK`; must end ≥15 + your new tests, all green.
  Lint: 8 findings today → 0.
- Tests first for every finding: write the failing test, watch it fail, then fix.
- No commits. No network: never run `claude`, `composio`, `gh`, `curl`, or `xr.research` without stubs.
- ≤60 tool calls; if you pass that, stop and report what is left.

## 0. Facts (verified by the orchestrator 2026-09-26)
- Findings with evidence: `/Users/hamed/Desktop/social-media-automation/X/docs/briefs/R0_findings_round1.md` (read it
  first; the "Fix scope" column is the spec). Reviewer's raw report: `R0_review_round1.md` beside it.
- `xr/rank.py:107-116` `claude_json` builds `claude -p … --tools "" --json-schema …`. Measured: MCP tools are still
  exposed without `--strict-mcp-config`. Inside a Claude Code session the child must not inherit `ANTHROPIC_BETAS`
  (HTTP 400) — pattern to copy: `../telegram/tg/llm.py:85-95` (`_child_env`).
- `xr/rank.py:90-104` `slug` + `resolve` make `id = f"{date}-{slug(title)}"`.
- `xr/store.py:50-77` `fresh`; `:84-88` `save_topics` (INSERT OR REPLACE); `:95-100` `unused_topics(platform, days=3)`
  uses `datetime.now` directly (add an optional `now` param; keep the default behaviour).
- `xr/sources.py:57-65` `hacker_news`, `:76-87` `github` (no per-query guard); `:108-120` `_follow_spill`;
  `:159-171` `run_composio`; `:174-181` `trends_momentum`; `:184-198` `run_trends`.
- Fetcher contract (`xr/research.py:40-48`): `(pillars, hours) -> (items, errors)`. `default_fetchers` wraps
  `hacker_news`/`github` as `(items, [])` — change those two to return `(items, errors)` directly.
- `xr/research.py:73-74` `normalize` calls `store.fresh`; `:76-85` `rank`; `:87-117` `write`.
- Trends fixture `tests/fixtures/trends.json`: 53 buckets, the last (`Sep 20–26, 2026`) has `partial_data: true`.

## 1. Deliverable
Fix findings 1-10 exactly as scoped in the findings file, plus:
- `pyproject.toml` (new): `[project]` name `x-automation`, `requires-python = ">=3.13"`, dependencies copied from
  `requirements.txt`; `[tool.ruff]` `target-version = "py313"`, `line-length = 120`. Do NOT add `select`/`ignore`
  that disables rules; fix the 8 findings in code. `# noqa` only where the broad catch is the design (a source node
  must never kill the run) and with a reason on the same line.
- `Store.fresh` signature: add `errors: list[str] | None = None` or return `(items, errors)` — your choice, but the
  graph must put bad-item errors into state `errors` and they must reach `research.json`.
- Finding 8: keep `research.json` + `research.md` + `items.json` writes atomic (write `*.tmp`, then `os.replace`).

### Tests to add (names are suggestions; one per behaviour)
- claude_json argv contains `--strict-mcp-config` and `--tools ""`; child env has no `ANTHROPIC_BETAS` (patch
  `subprocess.run`, assert the call).
- two topics with the same 60-char slug prefix get different ids; same evidence → same id.
- `unused_topics("x")` hides a new-day topic whose evidence overlaps a topic used on x; still shown for linkedin.
- bad URL item is dropped, reported, and the good item survives.
- `run_composio`: nonzero exit with no `results` → one error per call; short results list → error for each missing
  call; distinct (slug, pillar, lang) per call are attributed correctly (patch `subprocess.run`).
- unreadable spill file → error for that call, other calls kept.
- HN second query raises → first query's items kept + one error.
- rank failure on a day that already has topics → existing `research.json` unchanged, `research.failed.json` written.
- trends momentum on the fixture skips the partial bucket (assert the exact value you compute, and state it).

## 2. Rails
- May NOT change: existing test expectations (you may add assertions), the `x-research/1` fields already written,
  `pillars.json`, anything outside the worktree.
- `claude_json` stays the single place that spawns `claude`.
- No VPS hostnames/IPs in any file.

## 3. Report
Write `/Users/hamed/Desktop/social-media-automation/X/.worktrees/R0/R0_report_round1.md` using this skeleton:
Files touched (path | lines | what) · Deviations with reasons · Exact commands run · Verification (suite count,
ruff result) · Anything unverified. Every number must come from a command you ran.
