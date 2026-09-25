# X research + posting pipeline (LangGraph)

STATUS (2026-09-26): ✅ research graph built (bb6676e), live on the VPS · ⏳ x graph: shaped into rows R0, X0-X8 below,
none started · method: plan-and-execute skill (profile `docs/AGENT_PROFILE.md`, ledger `docs/REVIEW_LEDGER.md`,
handoff `HANDOFF.local.md`, local only because this repo is public).

Local rebuild of n8n template 14768 ("Auto-post trending X tweets with Gemini AI images, FLUX and Buffer"), aimed
at one niche and split so the research serves every platform, not only X.

## Inventory (measured 2026-09-26)
- Research graph: `xr/` 4 modules, reviewed + fixed in R0 (2026-09-26): 36 tests green, ruff clean.
- Research runs on the VPS (canonical store there, no cron, no GitHub auth → github source not running there).
  2026-09-25 VPS run: 9 topics, sources composio 318 / hn 16, 0 errors.
- Consumers: none. ../telegram has no `/topics`; ../linkedin has its own topic search.
- ../telegram bot (@mobina_ai_assistant_bot) is live on the same VPS with allow-listed users, inline buttons and
  `claude -p` on the subscription. It is the ready-made human-approval surface for X drafts (decision D5).
- Seats present: `claude` (subscription, no API key), `codex` 0.153.4, `ollama` qwen3.8:27b-mlx, `ruff` 0.16.9.
- Posting: Buffer GraphQL `https://api.buffer.com`, personal key (`BUFFER_API_KEY`), per developers.buffer.com
  2026-09-24 supports create/delete/retrieve posts and list channels. Free-plan API access and rate limits: unverified.
- Images: Higgsfield reachable headless on the VPS; user rule: Seedream 4.5 **unlimited only, zero credits**;
  `unlim.available` was false on 2026-09-25 → image row is gated.

## Open decisions (owner: user; rows that depend on one are skipped until it lands)
| # | Decision | Blocks | Default if unanswered |
|---|---|---|---|
| D1 | Supply `BUFFER_API_KEY` (in `.env`); which X handle is connected in Buffer | X0, X6 | — |
| D2 | EN and FA as two separate posts, or one bilingual post | X2 | two posts |
| D3 | Single tweets only, or threads too | X1, X2 | single only |
| D4 | Posts per day | X8 | 2 |
| D5 | Approval surface: Telegram bot buttons / Buffer drafts / terminal | X5 | Telegram bot |
| D6 | Buffer mode: save as draft, or add to queue | X6 | draft |
| D7 | Images, given the ONE Higgsfield account has no API/MCP unlimited (`unlim.available: false`, remaining null, re-checked 2026-09-26 via claude.ai connector): (a) no images, (b) spend credits, (c) pipeline writes the image prompt and the user renders it in the Higgsfield web app, (d) a free non-Higgsfield model | X7 | **DECIDED 2026-09-26: (a) no images for now**; revisit (c) if the web app shows unlimited |
| D8 | GitHub read-only token on the VPS | research github source | skip |
| D9 | `claude -p` on the subscription for a daily schedule is acceptable | X8 | manual runs only |

## Rows
Each row ≤1 plan-day. "Suite" = `.venv/bin/python -m unittest discover -s tests` plus `ruff check xr tests`.
Counts are "before → at least"; a row may add tests, never delete or weaken one.

| Id | Deliverable (one sentence) | May touch | Gate (proven by a run) | Depends | Status |
|---|---|---|---|---|---|
| R0 | Second-family review of the research graph + lint wired and clean | `xr/`, `tests/`, `pyproject.toml` | Codex findings triaged in `docs/briefs/R0_findings_round1.md`; REAL ones fixed; suite 15 → ≥15 green; ruff 8 → 0 | — | ✅ 2026-09-26: Codex found 10 (all REAL), re-check found 4 new + 3 partial, 2 rounds; suite 15 → 36, ruff 8 → 0; MCP isolation measured live |
| X0 | Prove the X-side environment: Buffer key lists channels (read-only), Higgsfield `unlim` read, `claude -p` answers | `docs/AGENT_PROFILE.md` only | each command's real output pasted in the profile | D1 | ⏳ |
| X1 | `xr/x_text.py`: X weighted length (URLs = 23, twitter-text v3 weights), fits-in-one check, EN + FA fixtures | `xr/x_text.py`, `tests/test_x_text.py` | tests incl. Persian, emoji, URL cases | D3 | ⏳ |
| X2 | `draft` node: topic → EN and FA post(s) via `claude -p --json-schema`, validated by X1, cites only topic evidence | `xr/x_draft.py`, `prompts/`, tests | tests with a stub LLM + one real draft pasted in the report | X1, D2 | ⏳ |
| X3 | `review` node: Claude critique + revise loop, max 2 rounds, rubric in `prompts/x_review.md` | `xr/x_review.py`, `prompts/`, tests | tests: pass / revise / give-up paths | X2 | ⏳ |
| X4 | x graph assembled with SQLite checkpointer: unused topics → draft → review → `interrupt()` before publish; CLI `xr.x run` / `xr.x resume` | `xr/x_graph.py`, tests | test: run pauses, new process resumes from checkpoint | X3 | ⏳ |
| X5 | Approval surface per D5 (default: bot sends draft with Approve / Edit / Reject buttons, answer resumes the graph) | X: `xr/x_approve.py`; ../telegram: one handler | test both sides; one real round trip to the allow-listed user | X4, D5 | ⏳ |
| X6 | `publish` node: Buffer create (draft or queue per D6), `Store.mark_used(id, "x")`, `runs/<date>/published.json`; refuses without approval | `xr/x_publish.py`, tests | tests with fake HTTP; one real Buffer call only on explicit ask | X5, D1, D6 | ⏳ |
| X7 | (parked by D7=a) `image` node: Seedream 4.5 unlimited only; checks `unlim.available` first and skips (never spends) when false | `xr/x_image.py`, tests | test: unlim false → no generation call | X4, D7 | ⏳ gated |
| X8 | VPS deploy + cron: daily research, then x graph up to the approval pause | VPS only (`-p` own project, no ports) | one scheduled run observed end-to-end to the approval message | X6, D4, D9 | ⏳ |

Order rationale: R0 first (the new graph builds on `Store` and `rank`; review them before stacking on them), X0 next
(it produces the evidence X6 needs), X1 has no dependencies and de-risks every draft.

## Design (blueprint, unchanged from 2026-09-24)
| n8n template | here |
|---|---|
| Schedule Trigger (3×/day) | cron on the VPS (X8) |
| Apify X trending scraper + Gemini fallback | research graph fan-out over niche sources; no X source (paid API) |
| Data Table "used trends" 24h | `data/research.db` items/topics/usage |
| Pick 2 random trends | `rank` (Claude) + `Store.unused_topics("x")` |
| Gemini tweet (pidgin) | `draft` (Claude), EN + FA |
| — | `review` (Claude), max 2 revise rounds |
| FLUX on HuggingFace + Dropbox link | `image` (Higgsfield Seedream 4.5 unlimited only) |
| Buffer MCP post | `publish` via Buffer GraphQL |
| — | human approval via `interrupt()` |

## Not in this plan (other repos)
- ../telegram: deployed bot is older than git HEAD (5629eea, 5d10e3f not deployed, measured 2026-09-26); CLAUDE.md
  says 30 tests, suite runs 36; `/topics` reading the research. Tracked in that repo, not here.
