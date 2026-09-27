r"""X (Twitter) weighted post length: the only place it is computed.

Rules are twitter-text v3 (`config/v3.json`, fetched 2026-09-26): max 280, code points in 0-4351, 8192-8205,
8208-8223, 8242-8247 weigh 1, everything else 2, an emoji sequence counts 2 as one unit, every URL counts 23,
text is NFC-normalised first. So Persian letters/digits and ZWNJ (U+200C) count 1; RLM/LRM (U+200F/U+200E) count 2.

Counting is delegated to PyPI `twitter-text-parser==3.0.0` (MIT, swen128/twitter-text-python, archived
2023-10-17). Measured 2026-09-26: it passes all 22 cases of the official v3 conformance section
(`tests/fixtures/twitter_text_v3_weighted.json`) on weightedLength, valid and validRangeEnd.
Its `regexp/emoji.py` does `import pkg_resources` (setuptools) without declaring the dependency; this venv has
no setuptools, so a one-function stand-in is registered only for that import and removed right after.
A setuptools pin was measured instead (2026-09-26, py3.13, fresh `python -I`) and rejected: 82.0.0-84.0.0 no longer
ship `pkg_resources` (ModuleNotFoundError); 80.9.0-81.0.0 print a UserWarning ("pkg_resources is deprecated as an
API ... slated for removal as early as 2025-11-30 ...") on every import; 78.1.1-79.0.1 raise a DeprecationWarning
that unittest prints; 67.2.0 is silent but is a 2023 build tool predating later security fixes. No clean pin exists.

Deviations from the library, both conservative:
- The library turns "\r\n" into "\n" before counting (v3 itself only NFC-normalises), so it undercounts; one is
  added back per "\r\n" occurrence.
- Lone surrogates (possible from json) make the library raise UnicodeEncodeError. `check()` reports them as
  "invalid_char"; `weighted_length()` raises ValueError("lone surrogate").
The bundled emoji data is Emoji 12.0 (2019), so newer emoji sequences overcount (e.g. a ZWJ sequence counted per
code point): the safe direction, never an over-length post.
"""
from __future__ import annotations

import importlib.resources
import importlib.util
import sys
import types

MAX_WEIGHTED = 280


def _import_parser():
    shimmed = False
    if "pkg_resources" not in sys.modules and importlib.util.find_spec("pkg_resources") is None:
        stub = types.ModuleType("pkg_resources")
        stub.resource_string = lambda pkg, name: importlib.resources.files(pkg).joinpath(name).read_bytes()
        sys.modules["pkg_resources"] = stub
        shimmed = True
    try:
        from twitter_text import parse_tweet
        from twitter_text.config import config
        from twitter_text.extract_urls import extract_urls
        from twitter_text.has_invalid_characters import has_invalid_characters
    finally:
        if shimmed:
            sys.modules.pop("pkg_resources", None)
    return parse_tweet, config["version3"], has_invalid_characters, extract_urls


_parse_tweet, _V3, _has_invalid, _extract_urls = _import_parser()


def extract_urls(text: str) -> list[str]:
    """URLs exactly as X recognises them (with or without protocol, any case, bare domains like evil.com)."""
    return list(_extract_urls(text))


def _has_lone_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def weighted_length(text: str) -> int:
    """Weighted X length. Raises ValueError("lone surrogate") if text holds an unpaired surrogate."""
    if _has_lone_surrogate(text):
        raise ValueError("lone surrogate")
    return _parse_tweet(text, _V3).weightedLength + text.count("\r\n")


def check(text: str) -> dict:
    if _has_lone_surrogate(text):
        safe = "".join("\ufffd" if 0xD800 <= ord(ch) <= 0xDFFF else ch for ch in text)
        weighted = weighted_length(safe)
        return {"weighted": weighted, "valid": False, "remaining": MAX_WEIGHTED - weighted, "reason": "invalid_char"}
    parsed = _parse_tweet(text, _V3)
    weighted = parsed.weightedLength + text.count("\r\n")
    if not text.strip():
        reason = "empty"
    elif _has_invalid(text) or (parsed.weightedLength <= MAX_WEIGHTED and not parsed.valid):
        reason = "invalid_char"
    elif weighted > MAX_WEIGHTED:
        reason = "too_long"
    else:
        reason = None
    return {"weighted": weighted, "valid": reason is None and parsed.valid,
            "remaining": MAX_WEIGHTED - weighted, "reason": reason}
