# T1 build brief — `/topics` and `/topic <n>` in the Telegram bot

## Builder environment
- Repo: ../telegram (PRIVATE, own CI/CD). Worktree: `/Users/hamed/Desktop/social-media-automation/telegram/.worktrees/T1`
  on branch `t1-topics`. Do not leave it.
- Python: `/Users/hamed/Desktop/social-media-automation/telegram/.venv/bin/python`, run from the worktree root.
- Suite: `env -u ANTHROPIC_BETAS .venv/bin/python -m unittest discover -s tests` → today `Ran 39 … OK`; must end ≥39 +
  yours. Lint as CI runs it: `.venv/bin/python -m pyflakes tg/*.py` (install pyflakes into the venv if missing — the
  only network you may use) → clean.
- Tests first. No commits, no push (a push to main DEPLOYS to production). No network besides the pyflakes install.
  Never run `python -m tg.bot` (the live bot shares the session; running it locally can get the logins cancelled).
- ≤60 tool calls; stop and report if over.

## 0. Facts (verified by the orchestrator 2026-09-26)
- Research contract (producer: ../X `xr/research.py`): `<research_dir>/<YYYY-MM-DD>/research.json`,
  `"schema": "x-research/1"`, keys `date, generated_at, window_hours, pillars, sources, items_collected, items_fresh,
  trends, errors, topics`. Each topic: `id, title, title_fa, pillar, summary, summary_fa, why_now, angles[],
  evidence[{title,url,source,signal,lang}], score (0-100), suitable_for[]`. Topics are sorted by score, descending.
  A day folder may also hold `research.failed.json` (ignore it). A day's research.json may have `topics: []`.
- Real sample (3 topics, trimmed): `/private/tmp/claude-501/-Users-hamed/3c878d55-f1f1-4406-be57-5c4dafbc3874/scratchpad/research_sample.json`
  → copy into `tests/fixtures/research_sample.json`.
- On the VPS the research lives at `/home/ubuntu/x-research/research/` (uid 1000, same as the container user). The
  container does not see it yet. Newest folder today: 2026-09-25 (no cron yet — research can be days old).
- `docker-compose.yml`: service `bot`, `user: "1000:1000"`, volumes list at lines ~20-24; the compose file lives in
  `/home/ubuntu/telegram-bot`, so `../x-research/research` resolves to the research dir.
- `tg/bot.py`: commands are `text.startswith("/dm" | "/post" | "/reset")` branches in `on_message` (~lines 129-159),
  then a catch-all `"/"` help reply (~160-167) that must list the new commands. Every inbound/outbound is logged with
  `log_conv(sender, direction, text, **extra)`. Allow-list check happens before any command.
- Telethon's `event.reply` uses its default parse mode (Markdown) unless `parse_mode` is passed.
- Telegram message limit: 4096 characters (`tg/post.py` TEXT_LIMIT).
- Persian bidi rule (persian-writing guide, MIT): a Persian line whose first strong character is Latin
  («OpenAI …», «Claude Code …») is laid out LTR. Prefix Persian lines with RLM U+200F to keep them RTL.

## 1. Deliverable
### 1.1 Files
- `tg/research.py` (new, pure, no Telethon import): `latest(research_dir) -> tuple[str, dict] | None` (newest
  `YYYY-MM-DD` folder whose research.json parses, has schema `x-research/1` and ≥1 topic; skip malformed ones);
  `format_topics(doc, limit=10) -> str`; `format_topic(doc, n) -> str` (1-based n). Both return Telegram-HTML.
- `tg/bot.py`: `/topics` and `/topic <n>` branches (allow-listed like every command), help text updated, `log_conv`.
  Reply with `parse_mode="html"` and `link_preview=False`.
- `docker-compose.yml`: add `- ../x-research/research:/app/research:ro` and `RESEARCH_DIR: /app/research`.
- `.env.example`: document `RESEARCH_DIR` (default `research` relative to cwd for local runs).
- `tests/test_research_view.py` (new) + `tests/fixtures/research_sample.json`.
- `CLAUDE.md`: commands table / Bot section lines for /topics and /topic, the mount, test count.

### 1.2 Output shape
- `/topics`: header `📚 Research <date> (<age> old)` where age is days since `date` (today → "today"), then one block per
  topic: `<n>. <b>title</b> (score)` + next line the Persian title with RLM prefix. Footer: `/topic <n> for details`.
  Must stay ≤4096 chars: drop trailing topics and say how many were omitted.
- `/topic <n>`: title (b), Persian title (RLM), pillar · score · suitable_for, summary, Persian summary (RLM), why_now,
  angles as `• ` lines, evidence as `<a href="URL">title</a> — source` lines. ≤4096 chars (truncate evidence first).
- Errors: no research dir / no valid day → "No research available yet." ; bad n → "Topic <n> not found (1-<max>)."

### 1.3 Security (reviewer will verify)
- Every research string is untrusted web-derived text: `html.escape` all of it (titles, summaries, angles, source).
- Links: only `http`/`https` URLs become `<a href>`; the href is escaped with `quote=True`; anything else is shown as
  escaped text, never a link.
- The mount is read-only; the bot never writes into the research dir.

### 1.4 Tests (red first)
- latest(): picks the newest valid day; skips a newer folder with broken JSON, wrong schema, or `topics: []`; returns
  None for a missing dir.
- format_topics(): contains every topic title escaped; Persian lines start with U+200F; a title containing
  `<b>x</b> & [a](http://evil)` appears escaped (no raw `<b>`); output ≤4096 for 60 long topics and reports omissions.
- format_topic(): `javascript:alert(1)` evidence URL is not a link; https URL is; n out of range → error text.
- Age: date == today → "today"; 2 days → "2 days".

## 2. Rails
- May NOT change: existing tests' expectations, `tg/post.py`, `tg/llm.py`, the send/DM flows, `.github/`.
- No VPS IPs or hostnames in any file (CLAUDE.md already names the host; do not add more).

## 3. Report
Write `/Users/hamed/Desktop/social-media-automation/telegram/.worktrees/T1/T1_report_round1.md`: files, exact commands,
suite line, pyflakes line, deviations, unverified.
