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
from datetime import datetime, timedelta, timezone

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


def hacker_news(pillars: list[dict], hours: int = 48) -> list[dict]:
    since = int(time.time()) - hours * 3600
    items = []
    for p in pillars:
        for q in p["en"]:
            items += parse_hn(_get_json(hn_url(q, since)), p["name"])
    return items


# --- GitHub (via the authenticated gh CLI) ------------------------------------------------------

def parse_github(doc: dict, pillar: str) -> list[dict]:
    return [{
        "source": "github", "title": r["full_name"], "url": r["html_url"],
        "snippet": (r.get("description") or "")[:300], "signal": _num(r.get("stargazers_count")),
        "published": r.get("created_at", ""), "lang": "en", "pillar": pillar,
    } for r in doc.get("items", [])]


def github(pillars: list[dict], days: int = 7, per_query: int = 8) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    items = []
    for p in pillars:
        for q in p.get("github", []):
            cmd = ["gh", "api", "-X", "GET", "search/repositories", "-f", f"q={q} created:>{since}",
                   "-f", "sort=stars", "-f", f"per_page={per_query}"]
            doc = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60).stdout)
            items += [i for i in parse_github(doc, p["name"]) if i["signal"] >= 5]
    return items


# --- Composio: news, web (EN + FA), Reddit, YouTube, Google Trends ------------------------------

def composio_calls(pillars: list[dict], hours: int = 48) -> list[tuple[str, dict, str, str]]:
    """(slug, args, pillar, lang) for one `composio execute --parallel` batch."""
    after = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
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


def _follow_spill(o):
    """The composio CLI spills large outputs to a file and leaves a pointer (same as ../linkedin)."""
    if isinstance(o, dict):
        if o.get("storedInFile") and o.get("outputFilePath"):
            try:
                with open(o["outputFilePath"], encoding="utf-8") as f:
                    return json.load(f)
            except OSError:
                return o
        return {k: _follow_spill(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_follow_spill(v) for v in o]
    return o


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
    cmd = ["composio", "execute", "--parallel"]
    for slug, args, _, _ in calls:
        cmd += [slug, "-d", json.dumps(args, ensure_ascii=False)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    doc = _follow_spill(json.loads(proc.stdout))
    items, errors = [], []
    for (slug, _, pillar, lang), r in zip(calls, doc.get("results", [])):
        if not r.get("successful"):
            errors.append(f"{slug} [{pillar}/{lang}]: {str(r.get('error'))[:160]}")
            continue
        items += parse_composio_result(slug, r.get("data") or {}, pillar, lang)
    return items, errors


def trends_momentum(doc: dict) -> dict | None:
    """Last week vs 12-week mean of Google Trends interest (relative per query; compare momentum only)."""
    tl = (((doc.get("results") or {}).get("interest_over_time") or {}).get("timeline_data")) or []
    vals = [_num(v["values"][0].get("extracted_value")) for v in tl if v.get("values")]
    if len(vals) < 4:
        return None
    last, base = vals[-1], sum(vals[-13:-1]) / len(vals[-13:-1])
    return {"last": last, "mean12": round(base, 1), "momentum": round(last / base, 2) if base else None}


def run_trends(pillars: list[dict]) -> tuple[dict, list[str]]:
    qs = [p["trends"] for p in pillars if p.get("trends")]
    cmd = ["composio", "execute", "--parallel"]
    for q in qs:
        cmd += ["COMPOSIO_SEARCH_TRENDS", "-d", json.dumps({"query": q})]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    doc = _follow_spill(json.loads(proc.stdout))
    out, errors = {}, []
    for q, r in zip(qs, doc.get("results", [])):
        m = trends_momentum(r.get("data") or {}) if r.get("successful") else None
        if m:
            out[q] = m
        else:
            errors.append(f"COMPOSIO_SEARCH_TRENDS [{q}]: {str(r.get('error') or 'no timeline')[:160]}")
    return out, errors
