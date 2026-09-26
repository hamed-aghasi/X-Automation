# X1 report — round 1 (2026-09-26)

## Files touched (worktree `.worktrees/X1`, branch `x1-x-text`, nothing committed)
- `xr/x_text.py` (new): `MAX_WEIGHTED = 280`, `weighted_length(text) -> int`, `check(text) -> dict`
  (`weighted`, `valid`, `remaining`, `reason` ∈ {None, "empty", "too_long", "invalid_char"}).
- `tests/test_x_text.py` (new): 13 tests (22 conformance subTests in one of them, plus 12 Persian/emoji/check tests).
- `tests/fixtures/twitter_text_v3_weighted.json` (new): 22 cases (text, weightedLength, valid, validRangeEnd),
  `_source` names `conformance/validate.yml` section `WeightedTweetsWithDiscountedEmojiCounterTest`,
  https://github.com/twitter/twitter-text/blob/master/conformance/validate.yml, Apache-2.0.
- `pyproject.toml`, `requirements.txt`: `twitter-text-parser==3.0.0` added.

## Library decision: ADOPT `twitter-text-parser==3.0.0` (wrapped)
All 22 v3 cases pass on weightedLength AND valid (and validRangeEnd):

| # | case | expected wl/valid | got | vre exp/got |
|---|------|------|-----|-----|
| 0 | Regular Tweet with url | 26/T | 26/T PASS | 16/16 |
| 1 | Just url | 23/T | 23/T PASS | 13/13 |
| 2 | Long tweet, overflow at 280 | 285/F | 285/F PASS | 279/279 |
| 3 | Long tweet, url in middle | 299/F | 299/F PASS | 283/283 |
| 4 | Long tweet, url at end | 289/F | 289/F PASS | 264/264 |
| 5 | 10 url string | 240/T | 240/T PASS | 299/299 |
| 6 | 160 CJK | 320/F | 320/F PASS | 139/139 |
| 7 | 160 emoji | 320/F | 320/F PASS | 279/279 |
| 8 | 3 latin + 160 CJK | 323/F | 323/F PASS | 140/140 |
| 9 | 282 chars w/ normalized char | 281/F | 281/F PASS | 280/280 |
| 10 | H + cat + smiley + family | 7/T | 7/T PASS | 14/14 |
| 11 | BMP emoji | 10/T | 10/T PASS | 9/9 |
| 12 | skin tone + ZWJ | 4/T | 4/T PASS | 8/8 |
| 13 | General Punctuation | 110/T | 110/T PASS | 109/109 |
| 14 | long invalid-label url + short url | 12079/F | 12079/F PASS | 279/279 |
| 15 | 64-char domain no protocol | 68/T | 68/T PASS | 67/67 |
| 16 | CJK host > 63 punycode | 358/F | 358/F PASS | 143/143 |
| 17 | CJK host < 63 punycode | 264/T | 264/T PASS | 183/183 |
| 18 | 140 family emoji | 280/T | 280/T PASS | 1539/1539 |
| 19 | keycap 1⃣ | 2/T | 2/T PASS | 1/1 |
| 20 | Unicode 10.0 emoji | 34/T | 34/T PASS | 47/47 |
| 21 | Unicode 9.0 emoji | 29/T | 29/T PASS | 30/30 |

**Caveat found:** the package does not import as installed. `twitter_text/regexp/emoji.py:5` does
`import pkg_resources` (setuptools) but the package declares no dependencies, and this venv has no setuptools →
`ModuleNotFoundError`. The table above was produced with a scratch shim for `pkg_resources.resource_string`.
`xr/x_text.py` registers the same one-function stand-in in `sys.modules` only when `pkg_resources` is absent,
only around the import, and removes it right after (so nothing else sees a fake `pkg_resources`).
Alternative the orchestrator may prefer: pin setuptools (a version that still ships `pkg_resources`) instead;
not tried, since installing it needed network the brief did not allow.

## Commands
```
/opt/homebrew/bin/python3 <scratchpad>/convert_v3.py <scratchpad>/twitter-text-validate.yml tests/fixtures/twitter_text_v3_weighted.json   # system PyYAML 6.0.3, not added to project
uv pip install --python /Users/hamed/Desktop/social-media-automation/X/.venv/bin/python twitter-text-parser==3.0.0
PYTHONPATH=<scratchpad>/shim .venv/bin/python <scratchpad>/lib_check.py tests/fixtures/twitter_text_v3_weighted.json   # 22/22
../../.venv/bin/python -m unittest discover -s tests
ruff check xr tests
```

## Results
- Red first: `tests.test_x_text` failed (ImportError, no `xr.x_text`) before the module existed.
- Suite: `Ran 49 tests in 0.165s` / `OK` (36 existing + 13 new).
- Ruff: `All checks passed!`

## Deviations
- The `pkg_resources` stand-in (above), not foreseen by the brief.
- The converter used the system Python's PyYAML (outside the project). PyYAML was not added to the project.
- Invisible characters in tests (ZWNJ, ZWJ, RLM, U+FFFE) are written as `\u` escapes, because ruff PLE2502 rejects a
  literal RLM.
- `check()`: `valid` is True only when `reason is None` and the library says valid. Precedence of reasons is
  empty > invalid_char > too_long. `remaining` can be negative.
- CLAUDE.md and docs/PLAN.md were not updated (outside the brief's file list); the orchestrator should update the
  test count (36 → 49) and X1 status.

## Unverified
- Whether X's live composer still matches v3 today: checked only against the official conformance file, not a
  live post.
- The library's emoji table is a bundled `emoji-test.txt` from 2023 or earlier. Emoji added to Unicode after that
  may be counted per code point (2 each) instead of 2 per sequence. Not tested.

# Round 2 (2026-09-26) — fixes from X1_findings_round1.md

## Tests first
I added 4 tests to `tests/test_x_text.py` (`CrlfTest`, `SurrogateTest`). Run before the fix: `Ran 17 tests`,
`FAILED (failures=3, errors=1)`.
- `"س"*279 + "\r\n"`: `weighted_length` gives 281, and `check` gives `{"weighted": 281, "valid": False, "remaining": -1, "reason": "too_long"}`.
- `"a\nb"` gives 3; `"a\r\nb\r\nc"` gives 7.
- `check("a\ud800b")` gives valid False, reason `invalid_char`, and raises no exception.
- `weighted_length("a\udfffb")` raises `ValueError("lone surrogate")`.

## Fixes (`xr/x_text.py`)
- #1 CRLF: both functions add `text.count("\r\n")` to the library's count. The `invalid_char` fallback now compares
  against the library's own count, so a CRLF-driven overflow reports `too_long`.
- #4 lone surrogates: `weighted_length` raises `ValueError("lone surrogate")`. `check` returns `invalid_char` with
  `weighted` computed after replacing each surrogate with U+FFFD (weight 2, so the count stays conservative).
- #3 docstring: says the bundled emoji data is Emoji 12.0 (2019), so newer emoji sequences overcount (the safe
  direction). The docstring is now raw (`r"""`) so the `\r\n` in it stays literal text.

## #2 setuptools pin: no clean version exists, so the shim is kept unchanged
Measured in a throwaway scratch venv (`uv venv --python 3.13`, CPython 3.13.13, plus `twitter-text-parser==3.0.0`,
deleted afterwards). I did not install setuptools into the project venv; `find_spec('setuptools')` still returns None.
The commands were `python -I -c "import twitter_text; ..."` and `python -I -W error -c "import twitter_text"`
(or `-W error::UserWarning`).

| setuptools | `import pkg_resources` | `import twitter_text` default | with warnings as errors |
|---|---|---|---|
| 84.0.0 (latest), 83.0.0, 82.0.0 | ModuleNotFoundError | fails | fails |
| 81.0.0, 80.9.0 | ok | works, prints UserWarning on every import | fails |
| 79.0.1, 78.1.1 | ok | works, silent by default; `-W default` (what unittest enables) prints 1 warning | fails (DeprecationWarning) |
| 75.8.0 | ok | works, silent by default | fails (DeprecationWarning) |
| 67.2.0 | ok | works | works, silent |

The UserWarning text (80.9.0 / 81.0.0), raised at `twitter_text/regexp/emoji.py:5`:
`UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.`
The DeprecationWarning text (75.8.0 to 79.0.1):
`DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html`

Why I rejected each option:
- 82 and later: no `pkg_resources`, so the library cannot import.
- 80.9 and 81: a UserWarning on every import.
- 78.1.1 and 79: a DeprecationWarning that the test run prints, and the pin would sit just below a removal that
  has already happened.
- 67.2.0: the only silent one, but it is a 2023 build tool pinned as a runtime dependency. From memory
  (unverified): it predates the fixes for CVE-2024-6345 (fixed in 70.0.0) and CVE-2025-47273 (fixed in 78.1.1).

The reason is recorded in the `x_text` docstring. `pyproject.toml` and `requirements.txt` are unchanged in round 2.

## Results
- Suite: `Ran 53 tests in 0.166s` / `OK` (36 existing + 17 X1).
- Ruff: `All checks passed!`

## Deviations (round 2)
- `check()` on text with a lone surrogate still returns an int `weighted`: surrogates are replaced with U+FFFD (2 each)
  for the count. The brief did not say what `weighted` should be in that case.
- I added a `"a\r\nb\r\nc"` → 7 and lone-LF test beyond the boundary case the brief asked for.
- The CVE claims about setuptools 67.2.0 come from memory and were not checked online (no network allowed).
- The worktree files show as staged (`A`) in `git status`. I did not stage them; I committed nothing.
