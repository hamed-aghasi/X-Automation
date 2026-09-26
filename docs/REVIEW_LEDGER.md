# Review ledger — X

One row per reviewed item. Claimed = findings the reviewer raised; real = REAL after triage.

| Item | Builder | Reviewer | Commit | Claimed → real | Verdict |
|---|---|---|---|---|---|
| R0 research graph | Opus subagent (worktree), 2 rounds | Codex gpt-6-astra read-only: review + re-check | (this commit) | round 1: 10 → 10 REAL; re-check: 7 → 7 REAL, 1 dismissed by design, 2 downgraded | ✅ merged |
| T1 /topics (telegram) | Opus subagent (worktree), 2 rounds | Codex gpt-6-astra read-only | telegram t1-topics (unmerged) | 9 → 7 REAL, 1 DISMISSED (threat model), 1 DOWNGRADED | ✅ reviewed, deploy pending |
| X1 x_text | Opus subagent (worktree), 2 rounds | Codex gpt-6-astra read-only | (this commit) | 4 → 3 REAL (1 downgraded to minor), 1 DOWNGRADED (emoji 12.0 overcount, safe direction) | ✅ merged |
