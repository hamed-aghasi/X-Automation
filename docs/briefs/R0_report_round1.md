# R0 build report — round 1 (2026-09-25)

Builder worktree: `.worktrees/R0` (branch `r0-review-fixes`). Nothing committed. No network commands run.

## Files touched

| path | lines (new file) | what |
|---|---|---|
| `xr/rank.py` | 8, 102-104, 110-126 | F1: `_child_env` strips `ANTHROPIC_BETAS`; `claude_json` adds `--strict-mcp-config`, `check=False`, `env=_child_env(os.environ)`. F2: id = `<date>-<slug>-<sha1(sorted evidence urls)[:6]>` |
| `xr/store.py` | 12, 32, 36, 50-77, 103, 106-117 | F4: `fresh(..., errors=None)` per-item guard (bad URL / missing field / non-numeric signal → dropped + reported). F3: `unused_topics(platform, days=3, now=None)` hides topics sharing any evidence URL with a topic used on that platform. UP017 |
| `xr/sources.py` | 15, 57-67, 80-95, 117-175, 213-218, 228-230, 240-247 | F7: `hacker_news`/`github` per-query guard, return `(items, errors)`. F6: `_follow_spill(o, errors)` records unreadable/undecodable spill files. F5: new `_composio_batch` validates the envelope (exit code, missing/short `results`, slug mismatch, per-call spill) and returns one `(result, None)` or `(None, reason)` per call; `run_composio`/`run_trends` use it with `zip(strict=True)`. F9: `trends_momentum` drops trailing `partial_data` buckets. UP017 |
| `xr/research.py` | 13-17, 38, 48-49, 58, 73, 77-80, 87-89, 104-111, 129-143, 145-146, 180 | fetchers pass `(items, errors)` through; normalize puts bad-item errors into state `errors`; F8: `_atomic_write` (tmp + `os.replace`) for all 3 files; rank failure sets `rank_failed`, and if the day's `research.json` already has topics, the day's files are kept and `research.failed.json` is written instead. Lint: `collections.abc.Callable`, 2 `# noqa: BLE001` with reasons (source node, trends node), rank catch narrowed to explicit types, ISC004 parenthesised, UP017 |
| `tests/test_research.py` | 2-10, 17, 92, 115, 171-340 | 14 new tests (class `ReviewFixes`); 1 existing assertion changed (see Deviations); UP017 |
| `pyproject.toml` | new, 12 lines | `[project]` x-automation, `>=3.13`, deps from requirements.txt; `[tool.ruff]` py313, line-length 120, no select/ignore |

## Deviations

1. **Existing expectation changed** — `test_resolve_drops_invented_evidence` asserted `id == "2026-09-24-kept"`. Finding 2's
   spec (id gets a 6-hex evidence suffix) makes that impossible to keep; now `assertRegex(..., r"^2026-09-24-kept-[0-9a-f]{6}$")`.
   The rail forbids changing expectations; the fix scope requires it. Orchestrator to confirm.
2. **Ruff 8 → 17 → 0, not 8 → 0**: with `target-version = "py313"` ruff reports 9 extra UP017 (`timezone.utc` → `UTC`).
   Fixed in code with `ruff --fix` (safe fix, no rule disabled).
3. F8 scope detail: when rank failed and topics exist, `items.json` and `research.md` are also left untouched (not only
   `research.json`), so the day's three files stay consistent; the failed run's doc (incl. errors, counts) is in
   `research.failed.json`. When no topics exist yet, behaviour is unchanged (existing test still green).
4. F5 extra: a result whose `slug` field is present and does not match the call's slug becomes an error for that call
   (guards positional mis-attribution). `run_trends` with zero trend queries now returns `({}, [])` without spawning.
5. Rank-node catch was narrowed to `(RuntimeError, ValueError, KeyError, TypeError, OSError, SubprocessError)` rather
   than `# noqa`, since it is not a source node.

## Trends value (F9)
Fixture: 53 buckets, last `Sep 20–26, 2026` partial (35) is dropped. last = Sep 13–19 = 28; 12-week mean of
Jun 21 … Sep 6 = 556/12 = 46.33 → `{"last": 28.0, "mean12": 46.3, "momentum": 0.6}` (asserted exactly).

## Exact commands run (from the worktree root)
- `/Users/hamed/Desktop/social-media-automation/X/.venv/bin/python -m unittest discover -s tests` — baseline `Ran 15 … OK`;
  after adding tests `Ran 29 … FAILED (failures=8, errors=7)` (all 14 new + the changed assertion); final `Ran 29 tests … OK`
  (run 4 times, all OK).
- `ruff check xr tests` (ruff 0.16.6, /opt/homebrew/bin/ruff) — baseline `Found 8 errors`; after pyproject `Found 9 errors`
  (UP017); `ruff check xr tests --fix` → `Found 17 errors (17 fixed, 0 remaining)`; final `All checks passed!`.

## Verification
- Suite: `Ran 29 tests in 0.023s` / `OK` (15 original + 14 new).
- Lint: `All checks passed!` with settings from `pyproject.toml` (confirmed via `ruff check --show-settings`).

## Unverified
- `--strict-mcp-config` behaviour and the `ANTHROPIC_BETAS` 400 were not re-measured here (no network); tests assert argv/env only.
- Real composio CLI envelope on nonzero exit / spill failures not exercised live; covered by patched `subprocess.run` only.
- ruff is not pinned in `pyproject.toml` dependencies (brief said "pins ruff" in findings footer but the deliverable
  spec lists only target/line-length); ruff 0.16.6 used.

## Round 2 (2026-09-25) — fixes from the Re-check table

### Files touched
| path | what |
|---|---|
| `xr/store.py` | #4: `fresh` coerces `signal` to float inside the per-item guard (bad signal → dropped + reported; mixed "10"/2 dedupe compares numbers) |
| `xr/sources.py` | #7: `parse_hn` / `parse_github` moved inside the per-query try; catch widened to `(OSError, ValueError, TypeError, AttributeError, KeyError)` (+ `SubprocessError` for gh). #5: `parse_composio_result` wrapped per call; malformed `data` → `"<slug> [<pillar>/<lang>]: malformed data: …"`, other calls kept |
| `xr/research.py` | N2: rank node back to `except Exception` with `# noqa: BLE001` + reason (sets `rank_failed`, always reaches `write`). N1: preserved-day branch also writes `items.failed.json` atomically. N3: `_atomic_write` uses `tempfile.NamedTemporaryFile(dir=path.parent, prefix=<name>., suffix=.tmp, delete=False)` then `os.replace`; temp file unlinked on write or replace failure. `import subprocess` removed (no longer used), `import tempfile` added |
| `pyproject.toml` | N4: `[dependency-groups] dev = ["ruff>=0.16,<0.17"]` |
| `tests/test_research.py` | new class `ReviewFixesRound2` with 7 tests (mixed signals, malformed composio data, HN `{"hits": null}`, GitHub `{"items": null}`, AttributeError ranker still writes, unique temp paths, temp cleanup on failure); `test_rank_failure_keeps_existing_topics` extended to assert `items.failed.json` content and the exact file set of the day dir |

### Exact commands run (worktree root)
- `/Users/hamed/Desktop/social-media-automation/X/.venv/bin/python -m unittest discover -s tests` — after adding tests:
  `Ran 36 tests … FAILED (failures=2, errors=6)` (7 new + extended test); after fixes: `Ran 36 tests in 0.030s` / `OK` (3 runs).
- `ruff check xr tests` — one `RUF059` in the new test (unused `d2`), fixed by asserting it; final `All checks passed!`.

### Verification
- Suite: `Ran 36 tests in 0.030s` / `OK` (29 from round 1 + 7 new).
- Lint: `All checks passed!` (ruff 0.16.6, within the new `>=0.16,<0.17` pin).

### Deviations
- N3 cleanup test additionally asserts that a failing `os.replace` leaves the directory empty (the brief asked for cleanup
  on failure; this is its test). No other deviations.
- `uv`/`pip` was not run to install the dev group; the pin is declarative only (no network).
