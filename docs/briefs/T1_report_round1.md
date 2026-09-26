# T1 report — round 1 (2026-09-26)

Worktree `/Users/hamed/Desktop/social-media-automation/telegram/.worktrees/T1`, branch `t1-topics`. Nothing committed or pushed.

## Files
- `tg/research.py` (new, pure; imports only stdlib + `tg.post.TEXT_LIMIT`): `latest`, `age_label`, `format_topics`,
  `format_topic`, `handle_command` (extra: parses `/topics` / `/topic <n>` and returns the reply, so the bot branch is 4 lines
  and the command logic is unit-tested without Telethon), constants `RLM`, `SCHEMA`, `NO_RESEARCH`.
- `tg/bot.py`: import; `research_dir = env.get("RESEARCH_DIR") or "research"`; `/topics` / `/topic` branch after the
  allow-list check and before the catch-all, logs `log_conv(sender, "topics", reply, cmd=...)`, replies
  `parse_mode="html", link_preview=False`; help text gains one line.
- `docker-compose.yml`: `RESEARCH_DIR: /app/research` + volume `../x-research/research:/app/research:ro`.
- `.env.example`: `RESEARCH_DIR=research` documented.
- `tests/test_research_view.py` (new, 18 tests) + `tests/fixtures/research_sample.json` (copied verbatim from scratchpad).
- `CLAUDE.md`: status line, commands (test count 57 + pyflakes line), Bot section, Map, tests list.

## Commands (run from worktree root)
```
env -u ANTHROPIC_BETAS ../../.venv/bin/python -m unittest discover -s tests   # red first: Ran 40, FAILED (errors=1) (ImportError)
env -u ANTHROPIC_BETAS ../../.venv/bin/python -m unittest discover -s tests   # Ran 57 tests in 0.027s  OK
../../.venv/bin/python -m pyflakes tg/*.py                                    # no output, exit 0
```
pyflakes was already installed in the venv (no network used).

## Behaviour notes
- Text nodes use `html.escape(quote=False)` (`<`, `>`, `&` escaped; apostrophes stay readable); hrefs use
  `html.escape(url, quote=True)`. A link needs scheme http/https, a netloc, and no whitespace/control chars; otherwise the
  URL is shown as escaped text in parentheses.
- `/topics`: blocks dropped from the end until ≤4096; `… N more topics not shown` counts both the limit=10 cut and
  size drops. Header `📚 Research <date> (today)` / `(N days old)` / `(1 day old)`.
- `/topic <n>`: shrink order is evidence lines first, then per-field caps 1500→800→400→200→100 chars (clipped before escaping,
  so tags are never cut). Angles capped at 10. `Usage: /topic &lt;n&gt;` for non-numeric n.
- Persian lines (title_fa, summary_fa) are RLM-prefixed; empty Persian fields are omitted rather than emitting a bare RLM.

## Deviations
- Added `handle_command` and `age_label` to `tg/research.py` beyond the three named functions (testability).
- Non-numeric `/topic x` returns a usage line (brief specified only the out-of-range message).
- Bot wiring test is a source-text check (bot.py handlers are closures inside `run()`, not importable without Telethon/network).

## Unverified
- Real Telegram rendering (HTML parse, RLM effect, link_preview off) — the bot was not run, per the rules.
- Length check uses Python `len` on the HTML source; Telegram counts UTF-16 units of the parsed text. Tag overhead makes this
  conservative in practice, but an all-emoji/astral payload could in theory differ.
- The VPS mount (`../x-research/research` existing and readable by uid 1000 inside the container) — not deployed.

## Round 2 (2026-09-26) — fixes #1 #7 #8 #2 #3 #4 #5 (#6 dismissed, #9 downgraded: unchanged)
Tests first: 9 new tests in `Round2Test` → red run `Ran 66 … FAILED (failures=4, errors=4)` (the `&` flood test
already passed with round-1 caps); after the rework `Ran 66 tests in 0.016s OK`. `../../.venv/bin/python -m pyflakes tg/*.py`
→ no output, exit 0.

- #1/#7/#8 (`tg/research.py`): `u16(s)` = UTF-16 code units of the final HTML. Both replies are built by `_Reply`, a
  running 4096-unit budget that only appends complete fragments (never slices HTML). `_fit(value, max_units)` shortens the
  decoded text char by char (escaping each char) and adds `…`, so output never ends inside an entity. Evidence ≤20,
  angles ≤10, built once (800 evidence entries: 0.0001 s). Order in /topic: title, fa title, meta, summary, fa summary,
  why_now, angles, evidence, so evidence is what drops first. /topics reserves room for the omission line + footer.
- #2/#3: header date = folder name from `latest()` (`format_topics(..., day=)`; doc["date"] is only a 10-unit-capped
  fallback). `/topic` arg must fullmatch `[0-9]{1,3}` else `Usage: /topic &lt;n&gt;` (tests: `²`, `۲`, 4,089 digits,
  `1000`, bare `/topic`; `002` → topic 2). Folder match is also ASCII `[0-9]{4}-[0-9]{2}-[0-9]{2}`.
- #4: `urlsplit` ValueError → escaped text; non-list `evidence`/`angles` and non-dict entries → skipped; non-str fields
  → `str()`; lone surrogates → `encode("utf-8", "replace")` (become `?`).
- #5: the whole scan in `latest()` is inside `except OSError` → None → "No research available yet."
- Tests assert every reply ≤4096 UTF-16 units and well-formed (every `&` a complete entity, only complete `<b>`/`<a>`
  tags, balanced).
- CLAUDE.md: 66 tests, "≤4096 UTF-16 units".

Deviations (round 2): `/topic` folder regex tightened to ASCII too; `_fit` counts the ellipsis in the budget; the
reviewer's "move filesystem work off the event loop" (#7) was not in the fix scope, so `handle_command` still runs
synchronously in the handler (reads one small JSON). Real fixture measures 509 units (/topics), 1,712 (/topic 1).
Unverified: Telegram-side parsing of the replies (bot not run).
