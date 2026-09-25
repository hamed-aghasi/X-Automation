# Agent profile — X

STATUS (2026-09-26): ✅ every command below was run once on the Mac and its output pasted; re-run at each resume.
VPS facts live in `HANDOFF.local.md` (this repo is public).

The plan-and-execute skill holds the method. This file holds the facts the method needs for THIS project.

## Prove the environment (run at every resume, step 1)

| Claim | Command | Last measured output (2026-09-26) |
|---|---|---|
| tools on PATH | `which codex ollama docker claude uv gh composio ruff` | all 8 found (codex /opt/homebrew/bin, uv + composio ~/.local/bin) |
| codex seat | `codex --version` | codex-cli 0.153.4 |
| local model | `ollama list` | qwen3.8:27b-mlx (18 GB) |
| secrets + local files ignored | `git check-ignore -v .env HANDOFF.local.md data/research.db research/2026-09-24 .venv` | all 5 ignored (.gitignore, HANDOFF via .git/info/exclude) |
| repo in sync | `git status -sb` | `## main...origin/main` |
| Buffer key works | (X0) list channels query | not yet — D1 |
| Higgsfield unlimited | (X0) `models_explore` → `unlim.available` | false on 2026-09-25 (handoff) — re-check |

## Suites and legs

| Suite | Command | Legs | Expected (2026-09-26) | What a green run WITHOUT the leg proves |
|---|---|---|---|---|
| unit | `.venv/bin/python -m unittest discover -s tests` | offline only | Ran 15, OK | parsing, store, rank mapping and graph wiring on fixtures; NOT that live sources still answer |
| live | `.venv/bin/python -m xr.research --no-rank` | network: HN, gh, composio | 0 errors (2026-09-24: 339 fresh) | — |
| live rank | `.venv/bin/python -m xr.research` | + `claude -p` | ~4 min, 5-10 topics | — |

Run `claude -p` checks with `env -u ANTHROPIC_BETAS` when inside a Claude Code session (else HTTP 400 long-context beta).

## Lint / format

```
ruff check xr tests   # 2026-09-26: 8 errors (baseline; R0 brings it to 0)
```

## Secrets

| File | Purpose | Gitignored? | Read by |
|---|---|---|---|
| `.env` | `BUFFER_API_KEY` (not yet present) | yes (.gitignore:2) | X0, X6 |
| `HANDOFF.local.md` | VPS + login details | yes (.git/info/exclude) | orchestrator only; never in a brief |

Public repo: grep staged files for `sk_live|glpat|AKIA|-----BEGIN` and the VPS address before every push.

## Paths

| What | Path |
|---|---|
| plan | `docs/PLAN.md` |
| briefs, reports, findings | `docs/briefs/` |
| ledger | `docs/REVIEW_LEDGER.md` |
| handoff | `HANDOFF.local.md` (local only) |
| worktrees | `.worktrees/<item>` (gitignored) |

## Builder rails specific to this project

- Never change: existing test expectations, the `x-research/1` research.json contract, `pillars.json`.
- Never call a paid or publishing endpoint in a test or build: Buffer create, Higgsfield generate, X API.
  Tests use stubs; real calls happen only in X0 (read-only) or on the user's explicit ask.
- LLM calls go through `rank.claude_json` style (`claude -p --json-schema`, `--tools ""`); no API keys in code.
- No VPS hostnames, IPs or account ids in any tracked file.
