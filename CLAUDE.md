# X

AI-niche research + X posting pipeline built on LangGraph. Research output is platform-agnostic and meant to be
read by the sibling pipelines (`../linkedin`, `../telegram`). Plan and status: `docs/PLAN.md`.

STATUS (2026-09-24): ✅ research graph built + run live (10 topics from 271 fresh items, 0 source errors, 15 tests
pass). ⏳ X drafting/posting graph not started.

## Commands (verified 2026-09-24)
```
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m unittest discover -s tests          # 15 tests, offline (fixtures are real Composio output)
.venv/bin/python -m xr.research                         # full run, ~4 min (~10 s sources, rest is claude -p rank)
.venv/bin/python -m xr.research --no-rank               # sources only, ~10 s
.venv/bin/python -m xr.research --only hn,github --no-trends   # subset of sources
```

## Map
- `pillars.json` the niche: per pillar `en` queries (HN, Reddit, YouTube, news, web), `fa` Persian web queries,
  `github` repo queries, `trends` Google Trends term. Edit this to change what gets researched.
- `xr/sources.py` fetchers: HN Algolia (direct), GitHub (`gh api`), one `composio execute --parallel` batch for
  news/Reddit/YouTube/web, Google Trends momentum
- `xr/store.py` `data/research.db` (SQLite): `items` (URL first_seen), `topics`, `usage(topic_id, platform)`.
  Consumers call `Store.unused_topics("<platform>")` / `Store.mark_used(id, "<platform>")`.
- `xr/rank.py` `claude -p --json-schema` clusters items into 5-10 topics (EN + FA title/summary, angles, score,
  suitable_for); evidence cited by item id and mapped back in code, so it cannot invent URLs
- `xr/research.py` the LangGraph: fetch_* + trends in parallel → normalize → rank → write
- `research/<date>/research.json` (contract, `"schema": "x-research/1"`), `research.md` (human), `items.json`

## Gotchas
- No ANTHROPIC_API_KEY on this machine: ranking uses `claude -p` on the subscription (`XR_MODEL`, default sonnet).
- HN Algolia `numericFilters` must be URL-encoded (`>` raw returns non-JSON). reddit.com public JSON is 403 →
  Reddit goes through Composio. `COMPOSIO_SEARCH_WEB` `site:x.com` → HTTP 501 and web search never returns
  x.com posts: there is NO X source (needs the paid API or a scraper).
- `COMPOSIO_SEARCH_NEWS` ignores `when`, and web search returns evergreen pages: `Store.fresh` drops anything
  published >7 days ago (undated kept). Persian web search yields few fresh items (17 on the first run); Persian
  text in topics is written by Claude from mostly English sources.
- Items are untrusted web content (prompt is fenced). Topics backed only by Reddit are unverified claims: check
  evidence before posting.
- Posting goes through Buffer (Composio), never the paid X API. The `x-twitter` Claude Code plugin is installed
  globally but costs per call (docs.x.com pricing, 2026-09-24): don't wire it in without asking.
- Never publish without an explicit ask (same rule as ../linkedin).
