"""Weekly scrape: find the top trending skincare and makeup products and their keywords.

Each ISO week (Monday to Sunday, UTC) is saved to data/weeks/<YYYY-Www>.json, and
data/index.json lists the saved weeks for the site.

    python scrape.py                 # fill any missing weeks of the last 6, refresh this week
    python scrape.py --weeks 12      # look further back
    python scrape.py --week 2026-W40 --refresh
    python scrape.py --fixture docs.json --week 2026-W44   # offline, from saved docs
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import sources  # noqa: E402
from analyze import MIN_THREADS, TOP_N, WeekAnalysis  # noqa: E402
from lexicon import SUBREDDITS  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
log = sources.log


# ---------------------------------------------------------------- weeks
def week_id(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def week_bounds(wid: str) -> tuple[datetime, datetime]:
    y, w = wid.split("-W")
    start = datetime.fromisocalendar(int(y), int(w), 1).replace(tzinfo=timezone.utc)
    return start, start + timedelta(days=7)


def load_week(wid: str, data_dir: Path) -> dict | None:
    p = data_dir / "weeks" / f"{wid}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def previous_weeks(wid: str, data_dir: Path, n: int) -> list[tuple[str, dict | None]]:
    start, _ = week_bounds(wid)
    out = []
    for k in range(n, 0, -1):
        pid = week_id((start - timedelta(days=7 * k)).date())
        out.append((pid, load_week(pid, data_dir)))
    return out


# ---------------------------------------------------------------- collect
def collect(start: datetime, end: datetime, args, recent: bool) -> tuple[list[dict], dict]:
    s, e = int(start.timestamp()), int(end.timestamp())
    docs, counts = [], {"pullpush": 0, "reddit": 0}
    for sub in SUBREDDITS:
        got = sources.pullpush(sub, s, e, "submission", args.post_pages, args.pause)
        got += sources.pullpush(sub, s, e, "comment", args.comment_pages, args.pause)
        counts["pullpush"] += len(got)
        log(f"  r/{sub}: {len(got)} from archive")
        docs += got
        if recent:
            direct = sources.reddit_direct(sub, s, e, pause=max(1.0, args.pause / 2))
            counts["reddit"] += len(direct)
            log(f"  r/{sub}: {len(direct)} from reddit.com")
            docs += direct
    return docs, counts


# ---------------------------------------------------------------- trend math
def _same_product(a: str, b: str) -> bool:
    ba, na = a.split("|", 1)
    bb, nb = b.split("|", 1)
    if ba != bb:
        return False
    return na == nb or na.startswith(nb + " ") or nb.startswith(na + " ")


def past_score(key: str, week: dict | None) -> float:
    if not week:
        return 0.0
    allp = week.get("all_products", {})
    if key in allp:
        return float(allp[key][0])
    best = 0.0
    for k, v in allp.items():
        if _same_product(key, k):
            best = max(best, float(v[0]))
    return best


def rank_category(products: list[dict], cat: str, prev: list[tuple[str, dict | None]]) -> list[dict]:
    have_prev = [w for _, w in prev[-4:] if w]
    pool = [p for p in products if p["category"] == cat]
    ranked = []
    for p in pool:
        base = (sum(past_score(p["key"], w) for w in have_prev) / len(have_prev)) if have_prev else None
        if base is None:
            growth = 0.0
        else:
            growth = max(-0.6, min(2.0, (p["score"] - base) / (base + 5)))
        p["baseline"] = None if base is None else round(base, 2)
        p["change_pct"] = None if not base else round(100 * (p["score"] - base) / base)
        p["is_new"] = bool(have_prev) and (base or 0) == 0
        p["trend_score"] = round(p["score"] * (1 + growth), 2)
        ranked.append(p)
    ranked.sort(key=lambda p: p["trend_score"], reverse=True)
    strong = [p for p in ranked if p["threads"] >= MIN_THREADS]
    top = strong[:TOP_N]
    if len(top) < TOP_N:  # quiet week: allow products seen in fewer threads
        top += [p for p in ranked if p not in top and p["threads"] >= 2][: TOP_N - len(top)]
    for i, p in enumerate(top, 1):
        p["rank"] = i
    return top


def trending_terms(current: dict[str, int], n_docs: int, past: list[tuple[dict, int]],
                   min_count: int, limit: int) -> list[dict]:
    """Terms that show up more than usual this week, scored like a z-score."""
    out = []
    for term, c in current.items():
        if c < min_count:
            continue
        if past:
            share = sum(pc.get(term, 0) / max(pn, 1) for pc, pn in past) / len(past)
            expected = share * n_docs
            z = (c - expected) / math.sqrt(expected + 1)
            prev = round(expected, 1)
            change = None if expected < 0.5 else round(100 * (c - expected) / expected)
        else:
            z, prev, change = float(c), None, None
        out.append({"label": term, "count": c, "expected": prev, "change_pct": change, "_z": z})
    out.sort(key=lambda r: r["_z"], reverse=True)
    for r in out:
        r.pop("_z")
    return [r for r in out if r["change_pct"] is None or r["change_pct"] > 0][:limit]


# ---------------------------------------------------------------- one week
def build_week(wid: str, args, data_dir: Path, now: datetime, amazon_cache: dict) -> dict | None:
    start, end = week_bounds(wid)
    partial = end > now
    stop = min(end, now)
    recent = stop >= now - timedelta(days=9)
    log(f"\n== {wid} ({start:%b %d} – {(end - timedelta(days=1)):%b %d}){' partial' if partial else ''}")

    if args.fixture:
        docs = json.loads(Path(args.fixture).read_text())
        counts = {"fixture": len(docs)}
    else:
        docs, counts = collect(start, stop, args, recent and not args.no_live)

    if len(docs) < 30:
        log(f"  only {len(docs)} posts and comments found; not saving {wid}")
        return None

    wa = WeekAnalysis(docs)
    products = wa.products()
    prev = previous_weeks(wid, data_dir, 8)
    live_extras = recent and not args.no_live and not args.fixture

    week = {
        "week": wid,
        "start": start.date().isoformat(),
        "end": (end - timedelta(days=1)).date().isoformat(),
        "partial": partial,
        "generated_at": now.isoformat(timespec="seconds"),
        "stats": {
            "posts": sum(d["kind"] == "post" for d in wa.docs),
            "comments": sum(d["kind"] == "comment" for d in wa.docs),
            "subreddits": dict(sorted(
                {s: sum(d.get("sub") == s for d in wa.docs) for s in SUBREDDITS}.items(),
                key=lambda kv: -kv[1])),
            "sources": counts,
            "products_found": len(products),
            "compared_weeks": [pid for pid, w in prev[-4:] if w],
        },
    }

    for cat in ("skincare", "makeup"):
        top = rank_category(products, cat, prev)
        items = []
        for p in top:
            info = wa.describe(p)
            if live_extras:
                info["keywords"]["search_terms"] = sources.google_suggestions(p["name"])
            history = [{"week": pid, "score": round(past_score(p["key"], w), 2) if w else None}
                       for pid, w in prev]
            history.append({"week": wid, "score": p["score"]})
            items.append({
                "rank": p["rank"], "key": p["key"], "name": p["name"], "brand": p["brand"],
                "category": cat, "score": p["score"], "trend_score": p["trend_score"],
                "mentions": p["mentions"], "threads": p["threads"], "upvotes": p["upvotes"],
                "baseline": p["baseline"], "change_pct": p["change_pct"], "is_new": p["is_new"],
                "history": history, **info,
            })
        week[cat] = items
        log(f"  top {cat}: " + "; ".join(f"{p['name']} ({p['threads']} threads)" for p in items))

    kc = wa.keyword_counts()
    flat = {label: c for group in kc.values() for label, c in group.items()}
    group_of = {label: g for g, labels in kc.items() for label in labels}
    past_kw = [({l: c for g in w.get("keyword_counts", {}).values() for l, c in g.items()},
                w["stats"]["posts"] + w["stats"]["comments"]) for _, w in prev[-4:] if w]
    n = len(wa.docs)
    tk = trending_terms(flat, n, past_kw, min_count=8, limit=14)
    for r in tk:
        r["group"] = group_of.get(r["label"])
    week["trending_keywords"] = tk

    tc = wa.term_counts()
    past_terms = [(w.get("term_counts", {}), w["stats"]["posts"] + w["stats"]["comments"])
                  for _, w in prev[-4:] if w]
    week["emerging_terms"] = trending_terms(tc, n, past_terms, min_count=5, limit=16)

    if live_extras:
        if not amazon_cache:
            for cat in ("skincare", "makeup"):
                amazon_cache[cat] = sources.amazon_movers(cat)
        if any(amazon_cache.values()):
            week["retail_movers"] = {"source": "Amazon Movers & Shakers",
                                     "fetched_at": now.isoformat(timespec="seconds"), **amazon_cache}

    week["keyword_counts"] = kc
    week["term_counts"] = tc
    week["all_products"] = {p["key"]: [p["score"], p["threads"], p["category"], p["name"]]
                            for p in products[:500]}
    return week


def write_index(data_dir: Path):
    rows = []
    for p in sorted((data_dir / "weeks").glob("*.json"), reverse=True):
        w = json.loads(p.read_text())
        rows.append({
            "week": w["week"], "start": w["start"], "end": w["end"], "partial": w.get("partial", False),
            "generated_at": w.get("generated_at"),
            "docs": w["stats"]["posts"] + w["stats"]["comments"],
            "top": {c: [x["name"] for x in w.get(c, [])] for c in ("skincare", "makeup")},
        })
    (data_dir / "index.json").write_text(json.dumps(
        {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "weeks": rows}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weeks", type=int, default=6, help="completed weeks to keep filled (default 6)")
    ap.add_argument("--week", help="build only this ISO week, e.g. 2026-W44")
    ap.add_argument("--refresh", action="store_true", help="rebuild weeks that already exist")
    ap.add_argument("--no-current", action="store_true", help="skip the week in progress")
    ap.add_argument("--no-live", action="store_true", help="archive only: skip reddit.com, Google and Amazon")
    ap.add_argument("--post-pages", type=int, default=2, help="pages of 100 posts per subreddit")
    ap.add_argument("--comment-pages", type=int, default=4, help="pages of 100 comments per subreddit")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between archive requests")
    ap.add_argument("--fixture", help="read docs from this JSON file instead of the internet")
    ap.add_argument("--data-dir", default=str(DATA))
    args = ap.parse_args(argv)

    data_dir = Path(args.data_dir)
    (data_dir / "weeks").mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    this_week = week_id(now.date())

    if args.week:
        todo = [args.week]
    else:
        start, _ = week_bounds(this_week)
        todo = [week_id((start - timedelta(days=7 * k)).date()) for k in range(args.weeks, 0, -1)]
        todo = [w for w in todo if args.refresh or load_week(w, data_dir) is None
                or load_week(w, data_dir).get("partial")]
        if not args.no_current:
            todo.append(this_week)

    log(f"Weeks to build: {', '.join(todo) or 'none'}")
    amazon_cache: dict = {}
    built = 0
    for wid in todo:
        t0 = time.time()
        week = build_week(wid, args, data_dir, now, amazon_cache)
        if week:
            (data_dir / "weeks" / f"{wid}.json").write_text(json.dumps(week, indent=1, ensure_ascii=False))
            built += 1
            log(f"  saved {wid} in {time.time() - t0:.0f}s")
    write_index(data_dir)
    log(f"\nDone: {built} week(s) saved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
