"""SQLite memory shared across runs and platforms (data/research.db).

items  — every URL ever collected, with first_seen, so re-runs only surface fresh material.
topics — every ranked topic, so the ranker is told what was already covered.
usage  — which platform used which topic (written by consumers: X, LinkedIn, Telegram ...).
"""
from __future__ import annotations

import json
import sqlite3
import urllib.parse
from datetime import datetime, timedelta, timezone

_DROP_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "ref_src", "si"}


def canonical_url(url: str) -> str:
    p = urllib.parse.urlsplit(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if k.lower() not in _DROP_PARAMS]
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((p.scheme.lower() or "https", host, path, urllib.parse.urlencode(q), ""))


def published_at(s: str) -> datetime | None:
    """Sources disagree on format: '...Z', '... UTC', '...+00:00', '....000Z'. Unparseable -> None."""
    s = (s or "").strip().replace(" UTC", "+00:00").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Store:
    def __init__(self, path: str = "data/research.db"):
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS items (url TEXT PRIMARY KEY, title TEXT, source TEXT, pillar TEXT,
                lang TEXT, first_seen TEXT, last_seen TEXT, signal REAL);
            CREATE TABLE IF NOT EXISTS topics (id TEXT PRIMARY KEY, date TEXT, title TEXT, pillar TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS usage (topic_id TEXT, platform TEXT, used_at TEXT,
                PRIMARY KEY (topic_id, platform));
        """)

    def fresh(self, items: list[dict], now: datetime, fresh_hours: int = 48, max_age_days: int = 7) -> list[dict]:
        """Drop items published more than `max_age_days` ago (COMPOSIO_SEARCH_NEWS ignores `when`, and
        web search returns evergreen pages; undated items are kept), dedupe by canonical URL (highest signal
        wins), record them, and drop anything first seen more than `fresh_hours` ago so the same story is
        not re-researched every day."""
        oldest = now - timedelta(days=max_age_days)
        best: dict[str, dict] = {}
        for i in items:
            pub = published_at(i.get("published", ""))
            if pub and pub < oldest:
                continue
            key = canonical_url(i["url"])
            if key not in best or i["signal"] > best[key]["signal"]:
                best[key] = {**i, "url": key}
        cutoff = _iso(now - timedelta(hours=fresh_hours))
        stamp = _iso(now)
        out = []
        for key, i in best.items():
            row = self.db.execute("SELECT first_seen FROM items WHERE url=?", (key,)).fetchone()
            first = row[0] if row else stamp
            self.db.execute(
                "INSERT INTO items VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET "
                "last_seen=excluded.last_seen, signal=max(signal, excluded.signal)",
                (key, i["title"], i["source"], i["pillar"], i["lang"], first, stamp, i["signal"]))
            if first >= cutoff:
                out.append({**i, "first_seen": first})
        self.db.commit()
        return out

    def recent_topics(self, now: datetime, days: int = 7) -> list[str]:
        since = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        return [r[0] for r in self.db.execute(
            "SELECT title FROM topics WHERE date >= ? ORDER BY date DESC", (since,))]

    def save_topics(self, date: str, topics: list[dict]) -> None:
        for t in topics:
            self.db.execute("INSERT OR REPLACE INTO topics VALUES (?,?,?,?,?)",
                            (t["id"], date, t["title"], t["pillar"], json.dumps(t, ensure_ascii=False)))
        self.db.commit()

    def mark_used(self, topic_id: str, platform: str, now: datetime | None = None) -> None:
        self.db.execute("INSERT OR REPLACE INTO usage VALUES (?,?,?)",
                        (topic_id, platform, _iso(now or datetime.now(timezone.utc))))
        self.db.commit()

    def unused_topics(self, platform: str, days: int = 3) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self.db.execute(
            "SELECT data FROM topics WHERE date >= ? AND id NOT IN "
            "(SELECT topic_id FROM usage WHERE platform=?) ORDER BY date DESC", (since, platform))
        return [json.loads(r[0]) for r in rows]
