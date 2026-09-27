# X2 + X3 build report, round 1 (2026-09-27)

Worktree `.worktrees/X2`, branch `x2-x3-draft-review`. Nothing committed.

## Files
New: `xr/x_draft.py`, `xr/x_review.py`, `xr/x_cli.py`, `prompts/x_draft.md`, `prompts/x_review.md`,
`tests/test_x_draft.py` (9 tests), `tests/test_x_review.py` (16 tests).
Copied unmodified (verified with `cmp`): `xr/vendor/__init__.py`, `xr/vendor/fa_lint.py`,
`prompts/persian-writing/EXCERPT.md`, `prompts/persian-writing/LICENSE`.
Modified: `pyproject.toml` (`extend-exclude = ["xr/vendor"]`), `CLAUDE.md` (test count on the command line, x_cli
command, 4 map lines).
Rails: `git diff` on existing tests, research/store/sources/x_text/rank, pillars.json = empty.

## Commands
```
../../.venv/bin/python -m unittest discover -s tests   -> Ran 78 tests in 0.183s / OK
ruff check xr tests                                    -> All checks passed!
../../.venv/bin/python -m xr.x_cli draft --research /Users/hamed/Desktop/social-media-automation/X/research/2026-09-24/research.json --topic 1 --lang both
../../.venv/bin/python -m xr.x_cli draft --research .../research.json --topic 3 --lang both
```
Tests went red first (import errors for the missing modules), then green.

## Live acceptance (section 1.6)
Output files: `runs/2026-09-24/<topic_id>/post_{en,fa}.json` in the worktree (gitignored).

Topic 1 (`2026-09-24-claude-opus-5-5-lands-near-frontier-performance-at-40-lower-`)
- EN: pass, 0 revisions, weighted 255. Scores 5/5/5/5.
  > Anthropic released Claude Opus 5.5, its first model since pledging to pace the frontier, and says it matches
  > Fable 5.1 on most tasks at 40% lower cost than Opus 5. Claude Code now defaults to it on $20 Pro and Team
  > Standard plans.
  >
  > https://anthropic.com/claude-opus-5-5
- FA: pass, 0 revisions, weighted 236, fa_issues `[]`. Scores 5/5/5/5.
  > آنتروپیک از Claude Opus 5.5 رونمایی کرد؛ در بیشتر کارها به سطح Fable 5.1 می‌رسد، اما ۴۰ درصد ارزان‌تر از Opus 5 تمام می‌شود. آنتروپیک می‌گوید این مدل یک مهاجرت ۶۸۰ هزار خطی کد را در کمتر از یک روز انجام داده است.
  > https://anthropic.com/claude-opus-5-5

Topic 3 (`2026-09-24-mcp-s-security-reckoning-15-000-public-servers-zero-governan`)
- EN: pass, 0 revisions, weighted 262. Scores 5/5/5/5.
  > OX Security found that 15,465 public MCP servers send credentials and traffic to China, Russia, and home
  > networks, with no consistent governance. Other reports cite hardcoded credentials and recurring authorization
  > failures in production. https://unite.ai/ox-security-finds-mcp-servers-reaching-china-russia-and-home-networks
- FA: pass after 2 revisions, weighted 252, fa_issues `[]` in all 3 rounds.
  > بررسی OX Security روی ۱۵٬۴۶۵ سرور عمومی MCP نشان داد اطلاعات و ترافیک بسیاری از آن‌ها بدون هیچ نظارتی به چین، روسیه و شبکه‌های خانگی می‌رسد؛ گزارش‌های دیگر از اعتبارنامه‌های هاردکد‌شده و شکست‌های مکرر در مجوزدهی MCP خبر می‌دهند.
  > https://unite.ai/ox-security-finds-mcp-servers-reaching-china-russia-and-home-networks
  - round 0 revise (accuracy): «احراز هویت» means authentication; the evidence is about authorization.
  - round 1 revise (ZWNJ): «هاردکدشده» should take a ZWNJ before «شده».
  - round 2 pass.

No run gave up; no run errored.

### Observations for the orchestrator (not fixed)
- Topic 3 EN reads as if all 15,465 servers leak ("15,465 public MCP servers send credentials..."). The topic summary
  is itself ambiguous, and the FA post says «بسیاری از آن‌ها» (many of them). The reviewer passed EN with accuracy 5,
  so the review can miss a scope overstatement like this.
- The round-1 FA fix put a ZWNJ after «د», which does not join to the next letter anyway. It is invisible and
  harmless, but the reviewer's rule was stricter than the orthography needs.
- Topic 1 FA starts with «آنتروپیک» and keeps `Claude Opus 5.5` / `Fable 5.1` / `Opus 5` in Latin with Persian digits
  for ۴۰ and ۶۸۰, as the rules require.

## Design notes
- The gates run before the LLM reviewer. When a gate fails, `review` returns `revise` with the gate issues and makes
  no LLM call (a test asserts this).
- `draft` raises `DraftRejected` (a ValueError) when `source_url` is not an evidence URL. `write_post` treats that as
  a failed round and redrafts with a `url` issue; other exceptions give status `error`.
- `fa_issues` clears `fa_lint.ISSUES` before and after each call. The linter records only the first Latin-digit token
  on a line, so `latin-digits` is recomputed here with the Latin-run filter (a token containing a Latin letter, or
  directly after a Latin word). Otherwise a filtered `GPT-6` would hide a real `40` later on the same line; a test
  covers this.
- Untrusted text is fenced as JSON with `</` escaped to `<\/`, so it cannot close the `<topic>` or `<revision>`
  fence. The post in the review prompt has `</post>` escaped the same way.
- FA prompts (draft and review) embed the whole 24 KB EXCERPT.md; EN prompts do not.

## Deviations
- `draft` appends the source URL if the model's text leaves it out, instead of rejecting. The URL must still be an
  evidence URL, and the gate still requires exactly one URL at the end.
- `feedback` is a dict `{"previous_text", "issues"}`, not only the issues list, so the redraft can see what it is
  fixing.
- Added `write_posts(topic, langs)` (a per-language wrapper used by the error-isolation test) and a `--runs` /
  `--max-rounds` option on the CLI (`--runs` lets the test write to a temp dir).
- `review()` results also carry `gated`, `check` and `fa_issues`. When a gate fails, `scores` is `{}`.
- The CLAUDE.md STATUS line still says 53 tests / X2-X8 pending. The brief allowed only commands and map lines, so
  that line is left for the orchestrator.

## Unverified
- Nothing from `docs/PLAN.md` was updated (orchestrator's job).
- The live runs used the default model (`XR_MODEL` unset, so sonnet). I did not check which model actually served
  them.
- The gave_up and error paths are covered only by stub tests. The live runs did not hit either.

---

# Round 2 (2026-09-27): fixes for the Codex findings in X2X3_findings_round1.md

## Suite / lint
```
../../.venv/bin/python -m unittest discover -s tests   -> Ran 87 tests in 0.250s / OK   (53 existing + 34 X2/X3)
ruff check xr tests                                    -> All checks passed!
```

## Fixes, by finding
- **1+8 URL gate.** `xr/x_text.py` gains `extract_urls(text)`. It wraps `twitter_text.extract_urls` and is imported inside the
  existing pkg_resources shim block, so the shim stays in one place. The gate now finds bare domains and any case,
  and requires exactly ONE URL, at the end, exact-match in the evidence, and equal to the draft's `source_url`.
  `draft` appends the URL when it is not among the extracted URLs. Before, a substring check let `A/extra` stand in
  for `A`; now that case gets `A` appended and is then gated for having two URLs. All evidence URLs in
  research/2026-09-24 round-trip exactly through the extractor (0 mismatches, measured).
- **2 scope rule.**
  - `prompts/x_review.md` rule 1 now says each number keeps its role (studied vs affected), and quantifiers and hedges are
    kept. Broader scope, or a number that cannot be mapped to the topic, is a BLOCKING accuracy issue.
  - Includes the exact negative example and the correct "An analysis of 15,465 public MCP servers found…" form.
  - The same line is in `prompts/x_draft.md` (both languages).
- **3 integration tests.** `LoopGateIntegrationTest` puts 9 invalid drafts through `write_post` with an always-pass
  reviewer, at round 0 and again at the last revision:
  - EN: overflow after URL append (285); bare `evil.com`; `HTTPS://evil.com/x`; two URLs.
  - FA: Latin opening; RLM prefix; ALM prefix; em dash; en dash.
  - Asserts status, text/check consistency, `gated`, and reviewer call counts.
- **4 FA opening.** `opens_persian`: skips format controls, whitespace, punctuation, symbols and marks. The first
  LETTER must be in U+0600-06FF / FB50-FDFF / FE70-FEFF, and a leading digit (Latin or Persian) fails.
- **5 evidence ids.**
  - Evidence is in the fenced topic JSON with ids e0, e1 …, and the draft schema is `{"text", "source_id"}`.
  - Code resolves the id to a URL; an unknown id raises `DraftRejected`.
  - The only evidence-derived value outside the fence is the code-generated preferred id.
  - A test puts a newline + "EDITOR OVERRIDE" into a URL and asserts it never appears outside `<topic>`.
- **6 severity + code verdict.**
  - Review issues carry `severity: blocking|minor`, and `decide()` sets the verdict in code: revise if any
    non-minor issue, accuracy < 4, or any score < 3 (a missing score counts as 0).
  - Gate issues are always blocking.
- **7 CLI isolation.**
  - Each language's loop, JSON write and console print run inside their own try/except.
  - JSON falls back to `ensure_ascii=True` on a lone surrogate. Console output uses `backslashreplace`.
  - The exit code is 1 only if a language failed to save or print.
  - Regression test: `--lang both` with a lone-surrogate EN draft on a strict UTF-8 stdout. EN ends as `gave_up`
    and FA as `pass`, and both files are written.
- **9 one candidate.** `text/source_url/check/rounds` all describe the last draft that was reviewed. `rounds` is that
  draft's round, so after a rejected last draft `rounds` can be lower than the number of drafts. Rejected drafts live
  only in `history`. Test: two revised drafts, then an unknown id, returns round 1's text with `rounds == 1`.

Mutation check (in memory, not saved), to show the new tests bite:
- `gates()` disabled: 18 failures in 2 integration tests.
- `decide()` always "pass": 4 failures.
- `opens_persian` always True: 5 failures.

## Live: topic 3 EN only
Status `pass`, 0 revisions, weighted 262. Scores: accuracy 5, clarity 5, voice 4, platform_fit 5. One minor issue
(voice: name OX Security explicitly), which does not block.
> An analysis of 15,465 public MCP servers found credentials and traffic reaching China, Russia, and home networks,
> with no consistent governance. Other reports cite hardcoded credentials and recurring authorization failures in
> production.
>
> https://unite.ai/ox-security-finds-mcp-servers-reaching-china-russia-and-home-networks

The scope error was **avoided**: the drafter used the correct form from the new rule, so the reviewer never saw a
wrong-scope post. Whether the reviewer would **catch** it was not tested live, because the brief allowed only this
one run. The round-1 file is kept beside it as `post_en.round1.json`.

## Deviations (round 2)
- **Not tests-first:** code came before the new tests. The failing state was shown instead by the mutation check above.
- **`verdict` removed from the review schema:** the code decides, so a model verdict could only contradict it.
- **`review()` takes an optional `source_url`**, which `write_post` passes.
- **`rounds` changed meaning:** it is now the returned candidate's round, not "revisions made" (finding 9).
- **`xr/x_text.py` was changed** (a round-1 rail) to add `extract_urls`, as the coordinator instructed.
- **The CLAUDE.md STATUS line was not touched.**

## Unverified (round 2)
- Live, the reviewer was not tested on a wrong-scope post (see above).
- Round 2 had no live FA run.
- Tests cover the CLI `ensure_ascii` fallback only via the stub.

---

# Round 3 (2026-09-27): per-call LLM timeout + one retry

- `xr/x_review.py`: `LLM_TIMEOUT = 180`; `call_llm(llm, prompt, schema)` calls `llm(prompt, schema, timeout=LLM_TIMEOUT)`
  and retries that same call once, on `subprocess.TimeoutExpired` only. Review calls it directly. `write_post` hands
  `draft` a wrapper that goes through `call_llm`, so draft calls get the same timeout and retry. The constant lives
  in x_review.py only; importing it into x_draft would be circular.
- Direct `x_draft.draft()` callers outside `write_post` still get claude_json's default timeout.
- `xr/rank.py` is untouched (`git diff --quiet` is clean), so ranking keeps 600 s.
- Tests (`TimeoutTest`, 4 new; StubLLM now records kwargs and can time out n times or always):
  - `timeout=180` reaches both calls.
  - One timeout, then success: the post passes and that step was called twice (draft and review).
  - Always timing out: status `error` with TimeoutExpired after exactly 2 calls on that step, and the next language
    still passes.
  - A non-timeout exception is not retried.
- `Ran 91 tests in 0.261s` / `OK`; ruff `All checks passed!`. No network this round.
- Worst case per step is now 2 × 180 s = 6 min instead of 10 min, and one stall is usually absorbed by the retry.
  Whether 180 s is enough for a slow but healthy FA draft was not measured; the only FA figures available are the
  orchestrator's 49-55 s.

---

# Round 4 (2026-09-27): `--effort medium` for draft/review

- `xr/rank.py` `claude_json` gains the optional keyword `effort: str | None = None`, which appends `["--effort", effort]`
  when set. With `effort=None`, argv is identical to before, so rank is unchanged. This is the only rank.py change (+4/-1).
- `xr/x_review.py`: `LLM_EFFORT = "medium"`; `call_llm` passes `timeout=LLM_TIMEOUT, effort=LLM_EFFORT` on the first
  call and on the retry. `LLM_TIMEOUT = 180` and the single retry are kept. A comment gives the orchestrator's
  measured reason (default slow and erratic; low misses the scope error 2/3; medium 11-14 s, catches it 3/3).
- Tests (+2 new, 1 renamed and extended):
  - timeout=180 and effort="medium" reach both the draft and review calls.
  - The retry keeps both kwargs.
  - With `subprocess.run` mocked, default argv has no `--effort` and still ends `--json-schema {}`; with
    `effort="medium"`, argv is exactly default + `["--effort", "medium"]`.
- `Ran 93 tests in 0.266s` / `OK`; ruff `All checks passed!`. No network.
- Unverified by me: the `--effort` flag's live behaviour (the orchestrator measured it).
