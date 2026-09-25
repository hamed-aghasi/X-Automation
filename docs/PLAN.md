# X research + posting pipeline (LangGraph)

STATUS (2026-09-24): ✅ research graph built + live run (research/2026-09-24: 10 topics, 0 errors) · ⏳ x graph not started

Local rebuild of n8n template 14768 ("Auto-post trending X tweets with Gemini AI images, FLUX and Buffer"),
re-aimed at one niche and split so the research is reusable by every platform, not just X.

## Scope (from the user, 2026-09-24)
- Niche: AI — Claude, ChatGPT, skills, MCP connections, AI automations, and adjacent topics.
- Audience: worldwide; output in English AND Persian.
- Research is a product in its own right: other platforms (../linkedin, ../telegram, later others) read it.
- Writing: Claude. Images: Higgsfield. Posting to X: Buffer (free tier), not the paid X API.

## n8n node → LangGraph node
| n8n template | here |
|---|---|
| Schedule Trigger (3×/day) | launchd job, shipped disabled (same as ../linkedin) |
| Apify X trending scraper + Gemini fallback | `collect` fan-out over niche sources (below); no country trend list |
| Data Table "used trends" 24h | SQLite `data/research.db`, seen-items + used-topics tables |
| Pick 2 random trends | `rank` — Claude scores/clusters, picks top N (not random) |
| Gemini tweet (pidgin) | `draft` — Claude, EN + FA variants |
| — | `review` — Claude critique, max 2 revise loops (new) |
| FLUX on HuggingFace + Dropbox link | `image` — Higgsfield |
| Buffer MCP post | `publish` — Buffer GraphQL API (`https://api.buffer.com`, Bearer `BUFFER_API_KEY` in .env) |
| — | `approve` — LangGraph `interrupt()` before publish (new) |

## Two graphs
1. **research graph** (platform-agnostic) — `collect → normalize/dedupe → rank → write`
   - Sources: Hacker News (Algolia API), Reddit (r/ClaudeAI, r/ChatGPT, r/LocalLLaMA, r/mcp, r/n8n …),
     GitHub (new/rising MCP-server and skills repos), YouTube + news + web + Google Trends via Composio
     (as ../linkedin does), X posts via web search `site:x.com` (no X API cost), Persian web search.
   - Output: `research/<date>/research.json` + `research.md` (topics, angle, evidence URLs, score, momentum).
     This is the contract other platforms consume.
2. **x graph** — `load research → pick → draft (EN+FA) → validate → review ⟲ → image → approve → publish`
   - SQLite checkpointer so a run paused at `approve` resumes later from the CLI.

## Blockers (need the user)
- Buffer: connect X inside Buffer, then create a personal API key at publish.buffer.com/settings/api → `.env`
  `BUFFER_API_KEY`. (Composio's buffer toolkit has no managed OAuth — it needs your own client id/secret, 2026-09-24.)
- Higgsfield headless: the local `higgsfield` MCP says "Needs authentication" (`claude mcp list`, 2026-09-24);
  only the claude.ai connector is live, which headless runs cannot use. One OAuth login fixes it.
- Claude: no ANTHROPIC_API_KEY on this machine, so Claude nodes call `claude -p` (subscription). Unverified
  whether that is acceptable for scheduled volume — decide before enabling launchd.

## Open decision
- Approval: default is `approve` interrupt ON (nothing reaches Buffer unreviewed); `--auto` flag to skip it.
