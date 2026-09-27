"""CLI for the X draft + review loop. Drafts only: it never posts anywhere.

    python -m xr.x_cli draft --research research/<date>/research.json --topic <n|id> [--lang en|fa|both]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from xr.rank import claude_json
from xr.x_review import write_post


def pick(topics: list[dict], sel: str) -> dict:
    """`sel` is a 1-based index into research.json topics[] or a topic id."""
    if sel.isdigit() and 1 <= int(sel) <= len(topics):
        return topics[int(sel) - 1]
    for t in topics:
        if t.get("id") == sel:
            return t
    raise SystemExit(f"topic {sel!r} not found ({len(topics)} topics)")


def safe_print(text: str) -> None:
    """Print without dying on text the console cannot encode (lone surrogates, a non-UTF-8 terminal)."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(text.encode(enc, "backslashreplace").decode(enc, "replace"))


def dump(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8").decode("utf-8")
    except UnicodeEncodeError:  # lone surrogate in model output: ASCII-escaped JSON is still valid JSON
        return json.dumps(obj, ensure_ascii=True, indent=2)


def emit(topic: dict, lang: str, post: dict, out_dir: Path) -> None:
    path = out_dir / f"post_{lang}.json"
    path.write_text(dump({"topic_id": topic["id"], **post}) + "\n", encoding="utf-8")
    weighted = (post.get("check") or {}).get("weighted")
    safe_print(f"\n[{lang}] status={post['status']} rounds={post['rounds']} weighted={weighted} -> {path}")
    if post.get("error"):
        safe_print(f"error: {post['error']}")
    safe_print(post.get("text") or "(no text)")


def main(argv=None, llm=claude_json) -> int:
    ap = argparse.ArgumentParser(prog="xr.x_cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    dr = sub.add_parser("draft", help="draft + review X posts for one topic")
    dr.add_argument("--research", required=True, type=Path)
    dr.add_argument("--topic", required=True, help="1-based index or topic id")
    dr.add_argument("--lang", choices=["en", "fa", "both"], default="both")
    dr.add_argument("--runs", type=Path, default=Path("runs"), help="output root (default: runs)")
    dr.add_argument("--max-rounds", type=int, default=2)
    args = ap.parse_args(argv)

    research = json.loads(args.research.read_text(encoding="utf-8"))
    topic = pick(research.get("topics", []), args.topic)
    out_dir = args.runs / research["date"] / topic["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    langs = ["en", "fa"] if args.lang == "both" else [args.lang]
    safe_print(f"topic: {topic['id']}")
    failed = False
    for lang in langs:  # each language is isolated end to end: loop, serialization and console output
        try:
            emit(topic, lang, write_post(topic, lang, llm=llm, max_rounds=args.max_rounds), out_dir)
        except Exception as exc:  # noqa: BLE001
            failed = True
            safe_print(f"\n[{lang}] failed while saving/printing: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
