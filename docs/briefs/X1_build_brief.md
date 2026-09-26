# X1 build brief — X weighted length (`xr/x_text.py`)

## Builder environment
- Worktree: `/Users/hamed/Desktop/social-media-automation/X/.worktrees/X1` on branch `x1-x-text`. Do not leave it.
- Python: `/Users/hamed/Desktop/social-media-automation/X/.venv/bin/python`, run from the worktree root.
- Suite: `.venv/bin/python -m unittest discover -s tests` → today `Ran 36 … OK`; must end ≥36 + yours, all green.
  Lint: `ruff check xr tests` → today `All checks passed!`; keep it.
- Tests first. No commits. ≤60 tool calls, stop and report if over.
- Network: allowed ONLY for `uv pip install` of a candidate package into the venv (see 1.2). No other network.

## 0. Facts (verified by the orchestrator 2026-09-26)
- X's official counting config, twitter-text `config/v3.json` (fetched 2026-09-26):
  `maxWeightedTweetLength 280, scale 100, defaultWeight 200, emojiParsingEnabled true, transformedURLLength 23`,
  weight-100 ranges `0-4351, 8192-8205, 8208-8223, 8242-8247`; every other code point weighs 200.
  So: Persian/Arabic letters (U+0600-06FF), Persian digits (U+06F0-06F9) and ZWNJ U+200C (8204) count 1 each;
  RLM U+200F (8207) and LRM U+200E (8206) are OUTSIDE the ranges and count 2; an emoji sequence counts 2 as one unit;
  every URL counts 23 whatever its length. Text is NFC-normalised before counting (twitter-text behaviour).
- Official conformance file (Apache-2.0, twitter/twitter-text): copied to
  `/private/tmp/claude-501/-Users-hamed/3c878d55-f1f1-4406-be57-5c4dafbc3874/scratchpad/twitter-text-validate.yml`.
  The v3 section is `WeightedTweetsWithDiscountedEmojiCounterTest` (starts at the line containing that key; ~24 cases
  with `weightedLength`, `valid`, `permillage`, `validRangeEnd` …). This section IS the spec.
- Candidate library: PyPI `twitter-text-parser` 3.0.0 (repo swen128/twitter-text-python, MIT, ARCHIVED, last push
  2023-10-17, no runtime deps, `requires_python >=3.7,<4`). X's v3 rules are unchanged since, so it may still be right.
- Decision D3 default: single posts only (no thread splitting in this row).
- Existing style: `xr/rank.py`, `xr/store.py` (small pure functions, type hints, module docstring that states
  measured facts with dates).

## 1. Deliverable
### 1.1 Files
- `xr/x_text.py` (new): the only place X length is computed.
- `tests/fixtures/twitter_text_v3_weighted.json` (new): the v3 conformance cases converted from the YAML (text +
  expected weightedLength + valid + validRangeEnd), with a `_source` field naming the upstream file, commit-less URL,
  and licence (Apache-2.0). Convert once with a throwaway script in the scratchpad; do not commit the script; do not
  add PyYAML to the project.
- `tests/test_x_text.py` (new).
- `pyproject.toml` + `requirements.txt`: only if you adopt the library (pin exact version).

### 1.2 Library or own code — decide by evidence
1. Install `twitter-text-parser==3.0.0` into the venv, run every converted conformance case through it.
2. If ALL cases pass (weightedLength AND valid): wrap it. Else: implement v3 yourself (URL extraction is the hard part;
   you may reuse the library's URL regex only if its licence text allows and you keep attribution in the docstring)
   and uninstall the package.
3. Report the per-case result of step 1 either way.

### 1.3 Contract
```python
MAX_WEIGHTED = 280
def weighted_length(text: str) -> int
def check(text: str) -> dict   # {"weighted": int, "valid": bool, "remaining": int, "reason": str | None}
                               # reason ∈ {None, "empty", "too_long", "invalid_char"}
```

### 1.4 Tests (red first)
- Every conformance case in the fixture (one subTest each): weightedLength and valid match.
- Persian: `"سلام"` → 4; a word with ZWNJ `"می‌خواهم"` counts the ZWNJ as 1; Persian digits `"۱۴۰۵"` → 4;
  RLM `"‏"` alone inside text counts 2; a 280-letter Persian string is valid, 281 is not; mixed
  `"Claude Code را امتحان کنید https://example.com/very/long/path"` counts the URL as 23.
- Emoji: `"👍🏽"` (skin-tone sequence) → 2; family ZWJ sequence → 2.
- `check("")` → reason "empty"; whitespace only → "empty".

## 2. Rails
- May NOT change: existing tests, `xr/research.py`, `xr/rank.py`, `xr/store.py`, `xr/sources.py`, `pillars.json`.
- No VPS names/IPs anywhere. No calls to claude, composio, gh, Buffer.

## 3. Report
Write `/Users/hamed/Desktop/social-media-automation/X/.worktrees/X1/X1_report_round1.md`: files touched, the
library decision with the per-case conformance table, exact commands, suite line, ruff line, deviations, unverified.
