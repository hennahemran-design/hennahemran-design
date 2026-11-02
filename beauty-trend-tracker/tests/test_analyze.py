"""Offline checks for product finding and keyword labelling. Run: python -m pytest tests"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scraper"))

from analyze import WeekAnalysis, find_mentions, clean  # noqa: E402
import scrape  # noqa: E402


def doc(i, text, sub="SkincareAddiction", score=5, thread=None, kind="comment"):
    return {"id": f"t1_{i}", "kind": kind, "sub": sub, "text": text, "score": score,
            "thread": thread or f"t3_{i}", "url": f"https://www.reddit.com/r/{sub}/{i}", "created": 0}


SAMPLES = [
    ("The Medicube Zero Pore Pads cleared my blackheads, holy grail for oily skin", "SkincareAddiction"),
    ("medicube zero pore pads are so gentle and my pores look smaller", "AsianBeauty"),
    ("Been using medicube zero pore pads for texture, love them", "SkincareAddiction"),
    ("Medicube zero pore pads broke me out though, too harsh for sensitive skin", "30PlusSkinCare"),
    ("Beauty of Joseon Relief Sun is lightweight with no white cast, perfect under makeup", "SkincareAddiction"),
    ("beauty of joseon relief sun is my favorite sunscreen for dry skin", "AsianBeauty"),
    ("BOJ relief sun, no white cast on deep skin, recommend", "SkincareAddiction"),
    ("Rare Beauty Soft Pinch Liquid Blush is so pigmented, one dot is enough. Buildable too", "MakeupAddiction"),
    ("rare beauty soft pinch liquid blush lasts all day and blends easily", "drugstoreMUA"),
    ("I love the rare beauty soft pinch liquid blush for a no-makeup look", "MakeupAddiction"),
    ("Rare beauty soft pinch liquid blush is overhyped imo, patchy on dry skin", "BeautyGuruChatter"),
    ("CeraVe products are fine", "SkincareAddiction"),
    ("elf halo glow liquid filter gives a glowy, dewy finish. great dupe for charlotte tilbury", "MakeupAddiction"),
    ("e.l.f. halo glow liquid filter is affordable and glowy", "drugstoreMUA"),
    ("Elf Halo Glow Liquid Filter oxidizes on me", "MakeupAddiction"),
]


def make_docs():
    docs = [doc(i, t, sub) for i, (t, sub) in enumerate(SAMPLES)]
    docs += [doc(100 + i, f"filler text about my routine number {i} today") for i in range(30)]
    return docs


def test_mentions_stop_at_breakers():
    got = list(find_mentions(clean("I love the CeraVe moisturizing cream, it's great")))
    assert got[0][0] == "CeraVe"
    assert got[0][1] == ("moisturizing", "cream")
    assert list(find_mentions(clean("CeraVe products are fine"))) == []


def test_products_found_and_categorized():
    wa = WeekAnalysis(make_docs())
    names = {p["name"]: p for p in wa.products()}
    assert "Medicube Zero Pore Pads" in names
    assert "Beauty of Joseon Relief Sun" in names
    assert "Rare Beauty Soft Pinch Liquid Blush" in names
    assert "e.l.f. Halo Glow Liquid Filter" in names
    assert names["Medicube Zero Pore Pads"]["category"] == "skincare"
    assert names["Rare Beauty Soft Pinch Liquid Blush"]["category"] == "makeup"
    assert names["Beauty of Joseon Relief Sun"]["threads"] == 3  # "BOJ" alias merged


def test_keywords_for_product():
    wa = WeekAnalysis(make_docs())
    p = next(p for p in wa.products() if p["name"] == "Beauty of Joseon Relief Sun")
    info = wa.describe(p)
    rec = {k["label"] for k in info["keywords"]["recommended_for"]}
    like = {k["label"] for k in info["keywords"]["people_like"]}
    assert "under makeup" in rec or "dry skin" in rec
    assert "no white cast" in like
    assert "white cast" not in {k["label"] for k in info["keywords"]["complaints"]}
    assert info["sentiment"]["positive"] > info["sentiment"]["negative"]
    assert info["quotes"]


def test_full_week_from_fixture(tmp_path):
    fx = tmp_path / "docs.json"
    fx.write_text(json.dumps(make_docs()))
    scrape.main(["--fixture", str(fx), "--week", "2026-W44", "--data-dir", str(tmp_path / "data")])
    week = json.loads((tmp_path / "data" / "weeks" / "2026-W44.json").read_text())
    assert week["skincare"] and week["makeup"]
    assert week["skincare"][0]["rank"] == 1
    index = json.loads((tmp_path / "data" / "index.json").read_text())
    assert index["weeks"][0]["week"] == "2026-W44"
