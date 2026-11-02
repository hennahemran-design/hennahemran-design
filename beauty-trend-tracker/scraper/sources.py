"""Fetchers for each data source. Every fetcher fails soft: on errors it logs and returns
what it has, so one blocked site never stops the weekly run."""

from __future__ import annotations

import json
import os
import re
import time
from html import unescape

import requests

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")
BOT_UA = "beauty-trend-tracker/1.0 (weekly research scraper; github.com/hennahemran-design)"

session = requests.Session()
session.headers["User-Agent"] = BOT_UA


def log(*a):
    print(*a, flush=True)


def _get(url, params=None, headers=None, tries=4, pause=2.0, timeout=30):
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            log(f"  ! {url} -> {e.__class__.__name__}")
            time.sleep(pause * 2 ** attempt)
            continue
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500, 502, 503, 504, 520, 522, 524):
            wait = float(r.headers.get("Retry-After") or pause * 2 ** attempt)
            log(f"  ! {r.status_code} from {url}, retrying in {wait:.0f}s")
            time.sleep(min(wait, 60))
            continue
        log(f"  ! {r.status_code} from {url}")
        return None
    return None


# ---------------------------------------------------------------- Reddit via Arctic Shift
# Arctic Shift (https://arctic-shift.photon-reddit.com) is a public Reddit archive that can
# search any date range, which is what lets the tracker fill in past weeks. reddit.com and
# PullPush both refuse requests from GitHub's servers; Arctic Shift doesn't.

ARCTIC = "https://arctic-shift.photon-reddit.com/api/{kind}/search"


def _doc_from_post(p: dict) -> dict:
    return {
        "id": "t3_" + str(p.get("id")),
        "kind": "post",
        "sub": p.get("subreddit"),
        "text": f"{p.get('title') or ''}\n{p.get('selftext') or ''}",
        "score": p.get("score") or 0,
        "thread": "t3_" + str(p.get("id")),
        "url": "https://www.reddit.com" + p["permalink"] if p.get("permalink") else None,
        "created": int(p.get("created_utc") or 0),
        "mod": _is_mod(p),
    }


def _is_mod(it: dict) -> bool:
    """Moderator notices and AutoModerator replies repeat the same rules text everywhere."""
    return (it.get("author") == "AutoModerator" or it.get("distinguished") == "moderator"
            or bool(it.get("stickied")))


def _doc_from_comment(c: dict) -> dict:
    link = c.get("link_id") or ""
    permalink = c.get("permalink")
    if not permalink and link:
        permalink = f"/r/{c.get('subreddit')}/comments/{link.replace('t3_', '')}/_/{c.get('id')}/"
    return {
        "id": "t1_" + str(c.get("id")),
        "kind": "comment",
        "sub": c.get("subreddit"),
        "text": c.get("body") or "",
        "score": c.get("score") or 0,
        "thread": link or None,
        "url": "https://www.reddit.com" + permalink if permalink else None,
        "created": int(c.get("created_utc") or 0),
        "mod": _is_mod(c),
    }


def arctic_shift(subreddit: str, start: int, end: int, kind: str, pages: int, pause: float) -> list[dict]:
    """kind is "posts" or "comments". Pages back from the end of the window, newest first."""
    out, before = [], end
    for _ in range(pages):
        r = _get(ARCTIC.format(kind=kind), params={
            "subreddit": subreddit, "after": start, "before": before, "limit": 100, "sort": "desc",
        }, pause=pause)
        time.sleep(pause)
        if r is None:
            break
        try:
            items = r.json().get("data") or []
        except ValueError:
            break
        if not items:
            break
        for it in items:
            if kind == "comments" and it.get("body") in ("[deleted]", "[removed]"):
                continue
            doc = _doc_from_comment(it) if kind == "comments" else _doc_from_post(it)
            if not doc["mod"]:
                out.append(doc)
        oldest = min(int(it.get("created_utc") or end) for it in items)
        if oldest <= start or len(items) < 100 or oldest >= before:
            break
        before = oldest
    return out


# ---------------------------------------------------------------- Bluesky
# Public post search, no account needed. Adds people outside Reddit.

BLUESKY = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
BLUESKY_QUERIES = ["skincare", "skin care", "makeup", "sunscreen", "moisturizer", "serum",
                   "foundation", "blush", "lip gloss", "mascara", "concealer", "sephora haul"]


def bluesky(start: int, end: int, pages: int, pause: float) -> list[dict]:
    from datetime import datetime, timezone
    iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for q in BLUESKY_QUERIES:
        cursor = None
        for _ in range(pages):
            params = {"q": q, "since": iso(start), "until": iso(end), "limit": 100, "sort": "top", "lang": "en"}
            if cursor:
                params["cursor"] = cursor
            r = _get(BLUESKY, params=params, pause=pause, tries=2)
            time.sleep(pause)
            if r is None:
                break
            try:
                data = r.json()
            except ValueError:
                break
            for p in data.get("posts", []):
                rec = p.get("record") or {}
                handle = (p.get("author") or {}).get("handle", "")
                rkey = p.get("uri", "").rsplit("/", 1)[-1]
                out.append({
                    "id": p.get("uri"), "kind": "post", "sub": "Bluesky", "text": rec.get("text") or "",
                    "score": int(p.get("likeCount") or 0) + int(p.get("repostCount") or 0),
                    "thread": p.get("uri"),
                    "url": f"https://bsky.app/profile/{handle}/post/{rkey}" if handle else None,
                    "created": 0,
                })
            cursor = data.get("cursor")
            if not cursor:
                break
    return out


# ---------------------------------------------------------------- Reddit directly
# Only used when REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are set (reddit.com blocks
# anonymous requests from GitHub's servers). Covers the newest days the archive may lack.

def reddit_enabled() -> bool:
    return bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))


def _reddit_base() -> tuple[str, dict]:
    cid, secret = os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")
    if cid and secret:
        try:
            r = requests.post("https://www.reddit.com/api/v1/access_token",
                              auth=(cid, secret), data={"grant_type": "client_credentials"},
                              headers={"User-Agent": BOT_UA}, timeout=30)
            token = r.json().get("access_token")
            if token:
                return "https://oauth.reddit.com", {"Authorization": f"bearer {token}"}
        except (requests.RequestException, ValueError) as e:
            log(f"  ! Reddit sign-in failed: {e}")
    return "https://www.reddit.com", {}


def _flatten_comments(children, sub, link, out, depth=0):
    for ch in children or []:
        if ch.get("kind") != "t1":
            continue
        c = ch["data"]
        c.setdefault("subreddit", sub)
        c.setdefault("link_id", link)
        if c.get("body") not in ("[deleted]", "[removed]"):
            out.append(_doc_from_comment(c))
        rep = c.get("replies")
        if depth < 2 and isinstance(rep, dict):
            _flatten_comments(rep["data"]["children"], sub, link, out, depth + 1)


def reddit_direct(subreddit: str, start: int, end: int, pause: float, comment_threads: int = 12) -> list[dict]:
    base, headers = _reddit_base()
    suffix = "" if "oauth" in base else ".json"
    posts, after = [], None
    for _ in range(10):
        r = _get(f"{base}/r/{subreddit}/new{suffix}", params={"limit": 100, "after": after, "raw_json": 1},
                 headers=headers, pause=pause, tries=2)
        time.sleep(pause)
        if r is None:
            break
        try:
            data = r.json()["data"]
        except (ValueError, KeyError):
            break
        kids = [k["data"] for k in data.get("children", [])]
        if not kids:
            break
        posts += [p for p in kids if start <= p.get("created_utc", 0) < end]
        if min(p.get("created_utc", 0) for p in kids) < start or not data.get("after"):
            break
        after = data["after"]
    docs = [_doc_from_post(p) for p in posts]
    for p in sorted(posts, key=lambda p: p.get("num_comments", 0), reverse=True)[:comment_threads]:
        r = _get(f"{base}/r/{subreddit}/comments/{p['id']}{suffix}",
                 params={"limit": 200, "depth": 3, "sort": "top", "raw_json": 1},
                 headers=headers, pause=pause, tries=2)
        time.sleep(pause)
        if r is None:
            continue
        try:
            listing = r.json()[1]["data"]["children"]
        except (ValueError, KeyError, IndexError):
            continue
        _flatten_comments(listing, subreddit, "t3_" + p["id"], docs)
    return docs


# ---------------------------------------------------------------- Google search suggestions
# What people type into Google next to a product's name.

def google_suggestions(name: str, pause: float = 1.0) -> list[str]:
    base = name.lower()
    found: dict[str, int] = {}
    for q in (base, f"{base} for", f"{base} vs", f"{base} dupe", f"is {base}"):
        r = _get("https://suggestqueries.google.com/complete/search",
                 params={"client": "firefox", "hl": "en", "gl": "us", "q": q},
                 headers={"User-Agent": UA}, tries=2, pause=pause)
        time.sleep(pause)
        if r is None:
            continue
        try:
            sugg = json.loads(r.content.decode("utf-8", "replace"))[1]
        except (ValueError, IndexError):
            continue
        for s in sugg:
            s = s.strip().lower()
            if s == base or s == q:
                continue
            found.setdefault(s, len(found))
    return sorted(found, key=found.get)[:12]


# ---------------------------------------------------------------- Amazon Movers & Shakers
# Products whose sales rank jumped the most in the last day. Amazon sometimes answers with
# a robot check instead; then this returns nothing and the site hides the panel.

AMAZON = {
    "skincare": "https://www.amazon.com/gp/movers-and-shakers/beauty/11060451",
    "makeup": "https://www.amazon.com/gp/movers-and-shakers/beauty/11058281",
}


def amazon_movers(category: str, limit: int = 10) -> list[dict]:
    r = _get(AMAZON[category], headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                         "Accept": "text/html,application/xhtml+xml"}, tries=2)
    if r is None or "captcha" in r.text.lower()[:5000]:
        log(f"  ! Amazon {category}: blocked or unavailable")
        return []
    html = r.text
    out, seen = [], set()

    def add(name, href, change):
        name = unescape(name).strip()
        if len(name) < 8 or name.lower() in seen:
            return
        seen.add(name.lower())
        short = re.split(r"\s[|\-–]\s|,\s", name)[0][:90]
        out.append({"rank": len(out) + 1, "name": short, "full_name": name,
                    "rank_change_pct": int(change.replace(",", "")) if change else None,
                    "url": "https://www.amazon.com" + href if href else AMAZON[category]})

    blocks = re.split(r'id="gridItemRoot"|data-asin="[A-Z0-9]{10}"', html)[1:]
    for block in blocks:
        alt = re.search(r'<img[^>]+alt="([^"]{8,})"', block)
        if alt:
            link = re.search(r'href="(/[^"]*?/dp/[A-Z0-9]{10})', block)
            change = re.search(r'(\d[\d,]*)%', block[:4000])
            add(alt.group(1), link.group(1) if link else None, change.group(1) if change else None)
        if len(out) >= limit:
            break
    if not out:  # layout changed: fall back to any product image that links to a product page
        for m in re.finditer(r'href="(/[^"]*?/dp/[A-Z0-9]{10})[^"]*"[^>]*>\s*(?:<[^>]+>\s*)*<img[^>]+alt="([^"]{8,})"', html):
            add(m.group(2), m.group(1), None)
            if len(out) >= limit:
                break
    log(f"  Amazon {category}: {len(out)} movers" + ("" if out else f" (page {len(html)} bytes, layout not recognised)"))
    return out
