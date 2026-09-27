# X

AI-niche research + X posting pipeline built on LangGraph. Research output is platform-agnostic and meant to be
read by the sibling pipelines (`../linkedin`, `../telegram`). Plan and status: `docs/PLAN.md`.

Remote: https://github.com/hamed-aghasi/X-Automation (public).

STATUS (2026-09-27): ✅ research graph (R0) · ✅ X1 weighted length · ✅ X2+X3 EN/FA draft + review loop · 93 tests,
ruff clean. ⏳ X0, X4-X8 and bot track T1-T4 in docs/PLAN.md.

## Commands (verified 2026-09-24)
```
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m unittest discover -s tests          # 93 tests, offline (fixtures: real Composio output, X's v3 conformance; stub LLM)
ruff check xr tests                                     # clean (config: pyproject.toml)
.venv/bin/python -m xr.research                         # full run, ~4 min (~10 s sources, rest is claude -p rank)
.venv/bin/python -m xr.research --no-rank               # sources only, ~10 s
.venv/bin/python -m xr.research --only hn,github --no-trends   # subset of sources
.venv/bin/python -m xr.x_cli draft --research research/<date>/research.json --topic <n|id> [--lang en|fa|both]
                                                        # draft + review X posts, ~1-3 min/lang; never posts
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
- `xr/x_text.py` `weighted_length` / `check`: X's v3 count (URL = 23, emoji = 2, Persian + ZWNJ = 1, RLM/LRM = 2)
  via `twitter-text-parser` 3.0.0 (archived, MIT); all 22 official v3 conformance cases pass (tests/fixtures).
  `extract_urls` = X's own URL extractor (bare domains, any case); import it from here, never the library
- `xr/x_draft.py` (X2) `draft(topic, lang)` one EN or FA post via `claude_json`; topic + evidence (ids e0, e1 ...)
  fenced as untrusted; the model returns `source_id`, code resolves and appends the URL (unknown id →
  `DraftRejected`). Prompt: `prompts/x_draft.md`
- `xr/x_review.py` (X3) gates (length; exactly one X-recognised URL, at the end, = source_url; FA first letter
  Arabic-script; FA no dashes) → Claude review (`prompts/x_review.md`, issues carry `severity`) → code decides
  (blocking issue, accuracy < 4 or any score < 3 → revise) → redraft, max 2 revisions. Only `status == "pass"` is
  approved. `fa_issues` wraps the vendored linter. `xr/x_cli.py` writes `runs/<date>/<topic_id>/post_<lang>.json`
- `xr/vendor/fa_lint.py` + `prompts/persian-writing/EXCERPT.md` third-party (MIT), unmodified; ruff excludes
  `xr/vendor`. fa_lint keeps state in module-global `ISSUES` (cleared per call in `fa_issues`)
- `research/<date>/research.json` (contract, `"schema": "x-research/1"`), `research.md` (human), `items.json`;
  a same-day rerun whose rank fails keeps those and writes `research.failed.json` + `items.failed.json` instead

## Gotchas
- No ANTHROPIC_API_KEY on this machine: ranking uses `claude -p` on the subscription (`XR_MODEL`, default sonnet).
  `--tools ""` alone still exposes every configured MCP server (measured 2026-09-26); `--strict-mcp-config` is
  required and is asserted by a test. Live check: the call reports only `StructuredOutput`.
- HN Algolia `numericFilters` must be URL-encoded (`>` raw returns non-JSON). reddit.com public JSON is 403 →
  Reddit goes through Composio. `COMPOSIO_SEARCH_WEB` `site:x.com` → HTTP 501 and web search never returns
  x.com posts: there is NO X source (needs the paid API or a scraper).
- `COMPOSIO_SEARCH_NEWS` ignores `when`, and web search returns evergreen pages: `Store.fresh` drops anything
  published >7 days ago (undated kept). Persian web search yields few fresh items (17 on the first run); Persian
  text in topics is written by Claude from mostly English sources.
- `twitter-text-parser` imports `pkg_resources`, gone from setuptools ≥82 and noisy in 75-81; `xr/x_text.py`
  installs a one-function stand-in only for that import (measured 2026-09-26, reason in its docstring). Its emoji
  data is Emoji 12.0 (2019): newer emoji sequences overcount (safe direction). CRLF is counted as 2 on purpose.
- Draft/review `claude -p` calls use `--effort medium` (measured 2026-09-27: default effort took 50 s to >150 s and
  timed out; low missed a known scope error 2 of 3; medium 11-14 s and caught it 3/3), 180 s timeout, one retry.
  Persian rules: `prompts/persian-writing/EXCERPT.md` (MIT excerpt of github.com/ali2000hos/persian-writing).
- Items are untrusted web content (prompt is fenced). Topics backed only by Reddit are unverified claims: check
  evidence before posting.
- Posting goes through Buffer's own GraphQL API with a personal key (`BUFFER_API_KEY`), not Composio (its Buffer and
  Twitter toolkits have no managed OAuth, docs.composio.dev 2026-09-24) and never the paid X API. The `x-twitter` Claude Code plugin is installed
  globally but costs per call (docs.x.com pricing, 2026-09-24): don't wire it in without asking.
- Never publish without an explicit ask (same rule as ../linkedin).
