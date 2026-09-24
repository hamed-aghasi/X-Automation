"""Research graph: sources (parallel) -> normalize -> rank -> write.

    .venv/bin/python -m xr.research [--hours 48] [--only hn,github] [--no-rank]

Output contract for every platform: research/<date>/research.json (schema "x-research/1").
"""
from __future__ import annotations

import argparse
import json
import operator
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from . import rank as rank_mod
from . import sources
from .store import Store

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "x-research/1"


class State(TypedDict, total=False):
    pillars: list[dict]
    hours: int
    items: Annotated[list[dict], operator.add]
    errors: Annotated[list[str], operator.add]
    source_counts: Annotated[dict, operator.or_]
    trends: dict
    fresh: list[dict]
    topics: list[dict]
    out_dir: str


# A fetcher takes (pillars, hours) and returns (items, errors).
Fetcher = Callable[[list[dict], int], tuple[list[dict], list[str]]]


def default_fetchers() -> dict[str, Fetcher]:
    return {
        "hn": lambda p, h: (sources.hacker_news(p, h), []),
        "github": lambda p, h: (sources.github(p, days=max(1, h // 24 * 3)), []),
        "composio": lambda p, h: sources.run_composio(sources.composio_calls(p, h)),
    }


def _source_node(name: str, fetch: Fetcher):
    def node(state: State) -> dict:
        try:
            items, errors = fetch(state["pillars"], state["hours"])
        except Exception as e:  # one dead source must not kill the run
            return {"errors": [f"{name}: {type(e).__name__}: {str(e)[:200]}"], "source_counts": {name: 0}}
        return {"items": items, "errors": errors, "source_counts": {name: len(items)}}
    node.__name__ = f"fetch_{name}"
    return node


def build_graph(fetchers: dict[str, Fetcher], trends_fn, store: Store, out_root: Path,
                now: datetime, ranker=rank_mod.rank, do_rank: bool = True):
    date = now.strftime("%Y-%m-%d")

    def trends(state: State) -> dict:
        try:
            t, errs = trends_fn(state["pillars"])
            return {"trends": t, "errors": errs}
        except Exception as e:
            return {"trends": {}, "errors": [f"trends: {type(e).__name__}: {str(e)[:200]}"]}

    def normalize(state: State) -> dict:
        return {"fresh": store.fresh(state.get("items", []), now, fresh_hours=state["hours"])}

    def rank(state: State) -> dict:
        if not do_rank:
            return {"topics": []}
        recent = store.recent_topics(now)
        try:
            topics = ranker(state["fresh"], state["pillars"], recent, state.get("trends", {}), state["hours"], date)
        except Exception as e:
            return {"topics": [], "errors": [f"rank: {type(e).__name__}: {str(e)[:300]}"]}
        store.save_topics(date, topics)
        return {"topics": topics}

    def write(state: State) -> dict:
        out = out_root / date
        out.mkdir(parents=True, exist_ok=True)
        doc = {
            "schema": SCHEMA_VERSION, "date": date,
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "window_hours": state["hours"],
            "pillars": [p["name"] for p in state["pillars"]],
            "sources": state.get("source_counts", {}), "items_collected": len(state.get("items", [])),
            "items_fresh": len(state["fresh"]), "trends": state.get("trends", {}),
            "errors": state.get("errors", []), "topics": state.get("topics", []),
        }
        (out / "research.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "items.json").write_text(json.dumps(state["fresh"], indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8")
        (out / "research.md").write_text(render_md(doc), encoding="utf-8")
        return {"out_dir": str(out)}

    g = StateGraph(State)
    for name, fetch in fetchers.items():
        g.add_node(f"fetch_{name}", _source_node(name, fetch))
        g.add_edge(START, f"fetch_{name}")
    g.add_node("trends", trends)
    g.add_edge(START, "trends")
    for n in ("normalize", "rank", "write"):
        g.add_node(n, {"normalize": normalize, "rank": rank, "write": write}[n])
    g.add_edge([f"fetch_{n}" for n in fetchers] + ["trends"], "normalize")  # fan-in: waits for all
    g.add_edge("normalize", "rank")
    g.add_edge("rank", "write")
    g.add_edge("write", END)
    return g.compile()


def render_md(doc: dict) -> str:
    L = [f"# Research {doc['date']}", "",
         f"Window {doc['window_hours']}h · {doc['items_fresh']} fresh of {doc['items_collected']} collected · "
         f"sources {json.dumps(doc['sources'])}", ""]
    if doc["trends"]:
        L += ["Trends momentum: " + ", ".join(f"{k} {v['momentum']}" for k, v in doc["trends"].items()), ""]
    for n, t in enumerate(doc["topics"], 1):
        L += [f"## {n}. {t['title']}  ({t['score']})", "",
              f"<div dir=\"rtl\">{t['title_fa']}</div>", "",
              f"**{t['pillar']}** · for {', '.join(t['suitable_for'])} · id `{t['id']}`", "",
              t["summary"], "", f"<div dir=\"rtl\">{t['summary_fa']}</div>", "",
              f"**Why now:** {t['why_now']}", "", "**Angles:**"] + [f"- {a}" for a in t["angles"]] + \
             ["", "**Evidence:**"] + [f"- [{e['title']}]({e['url']}) — {e['source']}" for e in t["evidence"]] + [""]
    if not doc["topics"]:
        L += ["_No topics ranked (see errors or --no-rank)._", ""]
    if doc["errors"]:
        L += ["## Errors", ""] + [f"- {e}" for e in doc["errors"]] + [""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="xr.research")
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--only", help="comma list of sources: hn,github,composio (trends always runs unless --no-trends)")
    ap.add_argument("--no-trends", action="store_true")
    ap.add_argument("--no-rank", action="store_true")
    ap.add_argument("--pillars", default=str(ROOT / "pillars.json"))
    ap.add_argument("--out", default=str(ROOT / "research"))
    ap.add_argument("--db", default=str(ROOT / "data" / "research.db"))
    a = ap.parse_args(argv)

    pillars = json.loads(Path(a.pillars).read_text(encoding="utf-8"))["pillars"]
    fetchers = default_fetchers()
    if a.only:
        fetchers = {k: v for k, v in fetchers.items() if k in a.only.split(",")}
    trends_fn = (lambda p: ({}, [])) if a.no_trends else sources.run_trends
    os.makedirs(os.path.dirname(a.db), exist_ok=True)
    graph = build_graph(fetchers, trends_fn, Store(a.db), Path(a.out), datetime.now(timezone.utc),
                        do_rank=not a.no_rank)
    final = graph.invoke({"pillars": pillars, "hours": a.hours})
    print(f"{final['out_dir']}: {len(final.get('topics', []))} topics, {len(final['fresh'])} fresh items, "
          f"sources {final.get('source_counts')}, {len(final.get('errors', []))} errors")
    for e in final.get("errors", []):
        print("  !", e)


if __name__ == "__main__":
    main()
