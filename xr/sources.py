"""Research sources. Each returns a list of Item dicts:
{source, title, url, snippet, signal, published, lang, pillar}.

Measured 2026-09-24: HN Algolia needs '>' URL-encoded; reddit.com public JSON answers 403 (so Reddit goes
through Composio); COMPOSIO_SEARCH_WEB with `site:x.com` fails with HTTP 501 and plain web search never
returns x.com posts, so there is no X source (would need the paid API or a scraper).
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta

UA = "x-research/0.1 (+social-media-automation)"


def _num(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


# --- Hacker News ---------------------------------------------------------------------------------

def hn_url(query: str, since_ts: int, min_points: int = 5, hits: int = 20) -> str:
    q = urllib.parse.urlencode({
        "query": query, "tags": "story", "hitsPerPage": hits,
        "numericFilters": f"created_at_i>{since_ts},points>{min_points}",
    })
    return "https://hn.algolia.com/api/v1/search?" + q


def parse_hn(doc: dict, pillar: str) -> list[dict]:
    out = []
    for h in doc.get("hits", []):
        oid = h.get("objectID")
        out.append({
            "source": "hn", "title": (h.get("title") or "").strip(),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={oid}",
            "discussion": f"https://news.ycombinator.com/item?id={oid}",
            "snippet": "", "signal": _num(h.get("points")) + 2 * _num(h.get("num_comments")),
            "published": h.get("created_at", ""), "lang": "en", "pillar": pillar,
        })
    return [i for i in out if i["title"]]


def hacker_news(pillars: list[dict], hours: int = 48) -> tuple[list[dict], list[str]]:
    """One failed query costs only that query: its error is reported, the other queries' items are kept."""
    since = int(time.time()) - hours * 3600
    items, errors = [], []
    for p in pillars:
        for q in p["en"]:
            try:
                items += parse_hn(_get_json(hn_url(q, since)), p["name"])
            except (OSError, ValueError, TypeError, AttributeError, KeyError) as e:  # network / JSON / shape
                errors.append(f"hn [{p['name']}] {q!r}: {type(e).__name__}: {str(e)[:160]}")
    return items, errors


# --- GitHub (via the authenticated gh CLI) ------------------------------------------------------

def parse_github(doc: dict, pillar: str) -> list[dict]:
    return [{
        "source": "github", "title": r["full_name"], "url": r["html_url"],
        "snippet": (r.get("description") or "")[:300], "signal": _num(r.get("stargazers_count")),
        "published": r.get("created_at", ""), "lang": "en", "pillar": pillar,
    } for r in doc.get("items", [])]


def github(pillars: list[dict], days: int = 7, per_query: int = 8) -> tuple[list[dict], list[str]]:
    since = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
    items, errors = [], []
    for p in pillars:
        for q in p.get("github", []):
            cmd = ["gh", "api", "-X", "GET", "search/repositories", "-f", f"q={q} created:>{since}",
                   "-f", "sort=stars", "-f", f"per_page={per_query}"]
            try:
                doc = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout)
                items += [i for i in parse_github(doc, p["name"]) if i["signal"] >= 5]
            except (subprocess.SubprocessError, OSError, ValueError, TypeError, AttributeError, KeyError) as e:
                detail = getattr(e, "stderr", None) or str(e)
                errors.append(f"github [{p['name']}] {q!r}: {type(e).__name__}: {str(detail)[:160]}")
    return items, errors


# --- Composio: news, web (EN + FA), Reddit, YouTube, Google Trends ------------------------------

def composio_calls(pillars: list[dict], hours: int = 48) -> list[tuple[str, dict, str, str]]:
    """(slug, args, pillar, lang) for one `composio execute --parallel` batch."""
    after = (datetime.now(UTC) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    calls = []
    for p in pillars:
        n = p["name"]
        for q in p["en"]:
            calls.append(("COMPOSIO_SEARCH_NEWS", {"query": q, "when": "2d"}, n, "en"))
            calls.append(("REDDIT_SEARCH_ACROSS_SUBREDDITS",
                          {"search_query": q, "limit": 10, "sort": "top", "time_filter": "week"}, n, "en"))
        calls.append(("YOUTUBE_SEARCH_YOU_TUBE",
                      {"q": p["en"][0], "maxResults": 8, "order": "viewCount", "publishedAfter": after}, n, "en"))
        calls.append(("COMPOSIO_SEARCH_WEB", {"query": p["en"][0] + " news this week"}, n, "en"))
        for q in p.get("fa", []):
            calls.append(("COMPOSIO_SEARCH_WEB", {"query": q}, n, "fa"))
    return calls


def _is_spill(o) -> bool:
    return isinstance(o, dict) and bool(o.get("storedInFile") and o.get("outputFilePath"))


def _follow_spill(o, errors: list[str]):
    """The composio CLI spills large outputs to a file and leaves a pointer (same as ../linkedin).
    An unreadable or undecodable spill file is appended to `errors` (the pointer is left in place)."""
    if isinstance(o, dict):
        if _is_spill(o):
            try:
                with open(o["outputFilePath"], encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError) as e:
                errors.append(f"unreadable spill file {o['outputFilePath']}: {type(e).__name__}: {str(e)[:100]}")
                return o
        return {k: _follow_spill(v, errors) for k, v in o.items()}
    if isinstance(o, list):
        return [_follow_spill(v, errors) for v in o]
    return o


def _composio_batch(slugs: list[str], args: list[dict]) -> list[tuple[dict | None, str | None]]:
    """Run one `composio execute --parallel` batch; return (result, None) or (None, reason) per call, in order.

    The envelope is validated rather than trusted: a nonzero exit keeps whatever per-call results came back,
    a missing/short `results` list yields an error for every call without a result (no silent zip truncation),
    and a spill failure costs only its own call."""
    cmd = ["composio", "execute", "--parallel"]
    for slug, a in zip(slugs, args, strict=True):
        cmd += [slug, "-d", json.dumps(a, ensure_ascii=False)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
    why = (f"composio exited {proc.returncode}: {(proc.stderr or '').strip()[:160]}" if proc.returncode
           else "no result in composio output")
    doc = None
    try:
        doc = json.loads(proc.stdout) if (proc.stdout or "").strip() else None
    except ValueError as e:
        why = f"{why}; unparseable output: {str(e)[:80]}"
    if _is_spill(doc):  # the whole envelope was spilled
        top: list[str] = []
        doc = _follow_spill(doc, top)
        why = "; ".join(top) or why
    results = doc.get("results") if isinstance(doc, dict) else None
    results = results if isinstance(results, list) else []
    out: list[tuple[dict | None, str | None]] = []
    for n, slug in enumerate(slugs):
        r = results[n] if n < len(results) else None
        if not isinstance(r, dict):
            out.append((None, why))
            continue
        if r.get("slug") not in (None, slug):
            out.append((None, f"result slug {r.get('slug')} does not match the call"))
            continue
        errs: list[str] = []
        r = _follow_spill(r, errs)
        out.append((None, errs[0]) if errs else (r, None))
    return out


def parse_composio_result(slug: str, data: dict, pillar: str, lang: str) -> list[dict]:
    base = {"pillar": pillar, "lang": lang}
    out = []
    if slug == "COMPOSIO_SEARCH_NEWS":
        for n in data.get("news_results", []):
            out.append({**base, "source": "news:" + str(n.get("source", "")), "title": n.get("title", ""),
                        "url": n.get("link", ""), "snippet": n.get("snippet", ""), "signal": 0.0,
                        "published": n.get("published_at", "")})
    elif slug == "REDDIT_SEARCH_ACROSS_SUBREDDITS":
        for p in data.get("posts", []):
            url = p.get("permalink", "")
            if url.startswith("/r/"):
                url = "https://www.reddit.com" + url
            out.append({**base, "source": "reddit:" + str(p.get("subreddit", "")), "title": p.get("title", ""),
                        "url": url, "snippet": (p.get("selftext") or "")[:300],
                        "signal": _num(p.get("score")) + 2 * _num(p.get("num_comments")),
                        "published": p.get("created_datetime", "")})
    elif slug == "YOUTUBE_SEARCH_YOU_TUBE":
        for it in data.get("items", []):
            vid = (it.get("id") or {}).get("videoId")
            sn = it.get("snippet") or {}
            if vid:
                out.append({**base, "source": "youtube:" + str(sn.get("channelTitle", "")),
                            "title": sn.get("title", ""), "url": f"https://www.youtube.com/watch?v={vid}",
                            "snippet": sn.get("description", ""), "signal": 0.0,
                            "published": sn.get("publishedAt", "")})
    elif slug == "COMPOSIO_SEARCH_WEB":
        for c in data.get("citations", []):
            out.append({**base, "source": "web", "title": c.get("title", ""), "url": c.get("url", ""),
                        "snippet": "", "signal": 0.0, "published": c.get("publishedDate", "")})
    for i in out:
        i["title"] = (i["title"] or "").strip()
        i["snippet"] = str(i["snippet"] or "")[:300].strip()
    return [i for i in out if i["title"] and i["url"]]


def run_composio(calls: list[tuple[str, dict, str, str]]) -> tuple[list[dict], list[str]]:
    batch = _composio_batch([c[0] for c in calls], [c[1] for c in calls])
    items, errors = [], []
    for (slug, _, pillar, lang), (r, why) in zip(calls, batch, strict=True):
        if r is None:
            errors.append(f"{slug} [{pillar}/{lang}]: {why}")
            continue
        if not r.get("successful"):
            errors.append(f"{slug} [{pillar}/{lang}]: {str(r.get('error'))[:160]}")
            continue
        try:
            items += parse_composio_result(slug, r.get("data") or {}, pillar, lang)
        except (TypeError, AttributeError, KeyError, ValueError) as e:  # malformed data costs only this call
            errors.append(f"{slug} [{pillar}/{lang}]: malformed data: {type(e).__name__}: {str(e)[:120]}")
    return items, errors


def trends_momentum(doc: dict) -> dict | None:
    """Last week vs 12-week mean of Google Trends interest (relative per query; compare momentum only)."""
    tl = list((((doc.get("results") or {}).get("interest_over_time") or {}).get("timeline_data")) or [])
    while tl and tl[-1].get("partial_data"):  # the running week is incomplete and would read as a fall
        tl.pop()
    vals = [_num(v["values"][0].get("extracted_value")) for v in tl if v.get("values")]
    if len(vals) < 4:
        return None
    last, base = vals[-1], sum(vals[-13:-1]) / len(vals[-13:-1])
    return {"last": last, "mean12": round(base, 1), "momentum": round(last / base, 2) if base else None}


def run_trends(pillars: list[dict]) -> tuple[dict, list[str]]:
    qs = [p["trends"] for p in pillars if p.get("trends")]
    if not qs:
        return {}, []
    batch = _composio_batch(["COMPOSIO_SEARCH_TRENDS"] * len(qs), [{"query": q} for q in qs])
    out, errors = {}, []
    for q, (r, why) in zip(qs, batch, strict=True):
        if r is None:
            errors.append(f"COMPOSIO_SEARCH_TRENDS [{q}]: {why}")
            continue
        m = trends_momentum(r.get("data") or {}) if r.get("successful") else None
        if m:
            out[q] = m
        else:
            errors.append(f"COMPOSIO_SEARCH_TRENDS [{q}]: {str(r.get('error') or 'no timeline')[:160]}")
    return out, errors
