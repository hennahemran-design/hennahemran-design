"""Turn a week of posts and comments into trending products and their keywords.

A "doc" is one post or comment:
    {"id", "kind": "post"|"comment", "sub", "text", "score", "thread", "url", "created"}

Products are found by anchoring on a known brand and reading the words that follow it
("medicube zero pore pads"). The most common spelling of each product wins, so new
products from known brands are picked up without a product list.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from lexicon import (
    BEAUTY_GENERIC, BRANDS, CATEGORY_WORDS, COMPLAINTS, GENERIC_AFTER_BRAND, MAKEUP_TYPES, NAME_BREAKERS, NEGATIVE,
    PEOPLE_LIKE, POSITIVE, RECOMMENDED_FOR, SKINCARE_TYPES, STOPWORDS, SUBREDDITS,
)

MAX_NAME_WORDS = 6
MIN_THREADS = 3          # a product needs this many separate threads to be ranked
TOP_N = 5

_URL = re.compile(r"https?://\S+|www\.\S+")
_MD = re.compile(r"[*_~>`#]+|\[([^\]]*)\]\([^)]*\)")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+|;\s*")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9'+%\-]*")
_WORD = re.compile(r"[a-z][a-z'\-]{2,}")
# A product name stops at punctuation other than spaces and hyphens.
_NAME_STOP = re.compile(r"[,()\[\]:\"!?.;/|\n]|\s-\s|\s+\+\s+")

_DOTTED = [("e.l.f.", "elf"), ("e.l.f", "elf"), ("dr. jart", "dr jart"), ("dr.jart", "dr jart"),
           ("r.e.m. beauty", "rem beauty"), ("l'oréal", "l'oreal")]

_ALIASES = sorted(BRANDS, key=len, reverse=True)
_BRAND_RE = re.compile(
    r"(?<![a-z0-9])(" + "|".join(re.escape(a) for a in _ALIASES) + r")(?![a-z0-9])"
)
_BRAND_WORDS = {w for a in BRANDS for w in re.split(r"[\s\-]+", a)}

_UPPER = {"spf", "pm", "am", "bha", "aha", "pha", "hd", "cc", "bb", "uv", "xl", "ha", "c",
          "spf30", "spf40", "spf50", "spf50+", "b5", "b3", "lrp", "ii", "iii", "sk-ii", "sa", "pa"}

_GROUPS = {
    "recommended_for": {k: [re.compile(p) for p in v] for k, v in RECOMMENDED_FOR.items()},
    "people_like": {k: [re.compile(p) for p in v] for k, v in PEOPLE_LIKE.items()},
    "complaints": {k: [re.compile(p) for p in v] for k, v in COMPLAINTS.items()},
}
_POS = [re.compile(p) for p in POSITIVE]
_NEG = [re.compile(p) for p in NEGATIVE]
_SKIN_MULTI = [t for t in SKINCARE_TYPES if " " in t]
_MAKEUP_MULTI = [t for t in MAKEUP_TYPES if " " in t]


def clean(text: str) -> str:
    text = text or ""
    text = text.replace("’", "'").replace("‘", "'").replace("&amp;", "&")
    text = _URL.sub(" ", text)
    text = _MD.sub(lambda m: m.group(1) or " ", text)
    text = text.lower()
    # brand names with dots would otherwise be cut by the sentence splitter
    for a, b in _DOTTED:
        text = text.replace(a, b)
    text = re.sub(r"\bmoisturis(er|ing|ers)\b", r"moisturiz\1", text)
    return text


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def display_name(brand: str, tokens: tuple[str, ...]) -> str:
    words = []
    for t in tokens:
        if t in _UPPER:
            words.append(t.upper())
        elif re.fullmatch(r"\d+%?|[\d.]+", t):
            words.append(t)
        else:
            words.append("-".join(p[:1].upper() + p[1:] for p in t.split("-")))
    return f"{brand} {' '.join(words)}".strip()


def product_key(brand: str, tokens: tuple[str, ...]) -> str:
    return f"{brand.lower()}|{' '.join(tokens)}"


def _continuation(rest: str) -> list[str]:
    """Words right after a brand mention that could be part of the product name."""
    stop = _NAME_STOP.search(rest)
    if stop:
        rest = rest[: stop.start()]
    out: list[str] = []
    for tok in _TOKEN.findall(rest):
        tok = tok.strip("'-")
        if not tok or tok in NAME_BREAKERS:
            break
        if not out and tok in GENERIC_AFTER_BRAND:
            break
        if _BRAND_RE.fullmatch(tok) and out:
            break
        out.append(tok)
        if len(out) >= MAX_NAME_WORDS:
            break
    # never end a name on a generic word ("cerave cream line")
    while out and out[-1] in GENERIC_AFTER_BRAND:
        out.pop()
    return out


def find_mentions(text: str):
    """Yield (brand_display, continuation_tokens, sentence_index) for one cleaned doc."""
    for si, sent in enumerate(sentences(text)):
        for m in _BRAND_RE.finditer(sent):
            cont = _continuation(sent[m.end():])
            if cont:
                yield BRANDS[m.group(1)], tuple(cont), si


def _category(tokens: tuple[str, ...], votes: Counter) -> str | None:
    joined = " ".join(tokens)
    skin = sum(t in SKINCARE_TYPES for t in tokens) + sum(m in joined for m in _SKIN_MULTI)
    make = sum(t in MAKEUP_TYPES for t in tokens) + sum(m in joined for m in _MAKEUP_MULTI)
    # words like "balm", "gel" or "lip" are in both lists; the context votes break ties
    if skin > make:
        return "skincare"
    if make > skin:
        return "makeup"
    total = votes["skincare"] + votes["makeup"]
    if total == 0:
        return None
    return "skincare" if votes["skincare"] >= votes["makeup"] else "makeup"


def _context_votes(sent: str) -> Counter:
    c = Counter()
    toks = set(_TOKEN.findall(sent))
    c["skincare"] += len(toks & SKINCARE_TYPES)
    c["makeup"] += len(toks & MAKEUP_TYPES)
    return c


class WeekAnalysis:
    def __init__(self, docs: list[dict]):
        # de-duplicate by id
        seen = {}
        for d in docs:
            seen[d["id"]] = d
        self.docs = list(seen.values())
        for d in self.docs:
            d["_clean"] = clean(d.get("text", ""))
            d["_sents"] = sentences(d["_clean"])
        self.phrase_docs: dict[tuple, set[int]] = defaultdict(set)
        self.phrase_sents: dict[tuple, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))
        self.cat_votes: dict[tuple, Counter] = defaultdict(Counter)
        self._index()
        self._corpus_df = self._doc_freq(range(len(self.docs)))

    # ---------- products ----------
    def _index(self):
        for i, d in enumerate(self.docs):
            sub_hint = SUBREDDITS.get(d.get("sub", ""), "mixed")
            for brand, cont, si in find_mentions(d["_clean"]):
                for k in range(1, len(cont) + 1):
                    ph = (brand,) + cont[:k]
                    self.phrase_docs[ph].add(i)
                    self.phrase_sents[ph][i].add(si)
                root = (brand,) + cont[:1]
                self.cat_votes[root] += _context_votes(d["_sents"][si])
                if sub_hint in ("skincare", "makeup"):
                    self.cat_votes[root][sub_hint] += 2

    def _threads(self, doc_ids) -> int:
        return len({self.docs[i].get("thread") or self.docs[i]["id"] for i in doc_ids})

    def _children(self, node: tuple) -> list[tuple]:
        n = len(node)
        return [p for p in self._by_len.get(n + 1, []) if p[:n] == node]

    def _select(self, node: tuple, docs: set[int], out: list):
        min_docs = 2
        kids = [c for c in self._children(node)
                if len(self.phrase_docs[c]) >= min_docs
                and len(self.phrase_docs[c]) >= 0.25 * len(self.phrase_docs[node])]
        if not kids:
            out.append((node, docs))
            return
        if len(kids) == 1 and len(self.phrase_docs[kids[0]]) >= 0.5 * len(self.phrase_docs[node]):
            # one spelling dominates: give it every mention of the shorter form too
            self._select(kids[0], docs, out)
            return
        for c in kids:
            self._select(c, set(self.phrase_docs[c]), out)

    def products(self) -> list[dict]:
        self._by_len: dict[int, list[tuple]] = defaultdict(list)
        for p in self.phrase_docs:
            self._by_len[len(p)].append(p)
        roots = [p for p in self._by_len.get(2, []) if self._threads(self.phrase_docs[p]) >= 2]
        chosen: list[tuple[tuple, set[int]]] = []
        for r in roots:
            self._select(r, set(self.phrase_docs[r]), chosen)

        merged: dict[str, dict] = {}
        for node, doc_ids in chosen:
            brand, tokens = node[0], node[1:]
            if len(tokens) == 1 and (tokens[0] in CATEGORY_WORDS or tokens[0].isdigit()):
                continue  # "CeraVe Moisturizer" names a category, not one product
            cat = _category(tokens, self.cat_votes[node[:2]])
            if cat is None:
                continue
            key = product_key(brand, tokens)
            if key in merged:
                merged[key]["_docs"] |= doc_ids
                continue
            merged[key] = {"key": key, "brand": brand, "tokens": tokens,
                           "name": display_name(brand, tokens), "category": cat,
                           "_node": node, "_docs": set(doc_ids)}
        out = []
        for p in merged.values():
            ids = p["_docs"]
            threads = self._threads(ids)
            upvotes = sum(max(int(self.docs[i].get("score") or 0), 0) for i in ids)
            engagement = sum(math.log1p(max(int(self.docs[i].get("score") or 0), 0)) for i in ids)
            p["mentions"] = len(ids)
            p["threads"] = threads
            p["upvotes"] = upvotes
            p["score"] = round(threads + 0.4 * (len(ids) - threads) + 0.25 * engagement, 2)
            out.append(p)
        out.sort(key=lambda p: p["score"], reverse=True)
        return out

    # ---------- keywords ----------
    def contexts(self, product: dict) -> dict[int, str]:
        """Text around each mention of a product, keyed by doc index."""
        node = product["_node"]
        ctx = {}
        for i in product["_docs"]:
            d = self.docs[i]
            if len(d["_clean"]) <= 400:
                ctx[i] = d["_clean"]
                continue
            sents = d["_sents"]
            idx = set()
            for ph in (node, node[:2]):
                idx |= self.phrase_sents.get(ph, {}).get(i, set())
            if not idx:
                ctx[i] = " ".join(sents[:3])
                continue
            keep = sorted({j for s in idx for j in (s - 1, s, s + 1) if 0 <= j < len(sents)})
            ctx[i] = " ".join(sents[j] for j in keep)
        return ctx

    @staticmethod
    def _terms(text: str) -> set[str]:
        """Single words and two-word phrases. Phrases only join words that sit side by side."""
        words = [w.strip("'-") for w in _WORD.findall(text)]
        ok = [bool(w) and w not in STOPWORDS and w not in _BRAND_WORDS for w in words]
        terms = {w for w, k in zip(words, ok) if k and w not in BEAUTY_GENERIC}
        for (a, ka), (b, kb) in zip(zip(words, ok), zip(words[1:], ok[1:])):
            if ka and kb and a != b and not (a in BEAUTY_GENERIC and b in BEAUTY_GENERIC):
                terms.add(f"{a} {b}")
        return terms

    def _doc_freq(self, ids) -> Counter:
        df = Counter()
        for i in ids:
            df.update(self._terms(self.docs[i]["_clean"]))
        return df

    def keyword_groups(self, texts: list[str]) -> dict[str, list[dict]]:
        n = max(len(texts), 1)
        out = {}
        for group, labels in _GROUPS.items():
            counts = Counter()
            for t in texts:
                for label, pats in labels.items():
                    if any(p.search(t) for p in pats):
                        counts[label] += 1
            floor = 2 if n >= 6 else 1
            out[group] = [{"label": k, "count": v, "share": round(v / n, 3)}
                          for k, v in counts.most_common(8) if v >= floor]
        return out

    def trending_alongside(self, product: dict, texts: list[str], limit: int = 10) -> list[dict]:
        n_ctx = len(texts)
        if n_ctx == 0:
            return []
        name_words = set(product["tokens"]) | set(product["brand"].lower().split())
        df = Counter()
        for t in texts:
            df.update(self._terms(t))
        n_all = len(self.docs)
        floor = max(2, math.ceil(0.08 * n_ctx))
        scored = []
        for term, c in df.items():
            if c < floor:
                continue
            parts = term.split()
            if any(p in name_words for p in parts):
                continue
            lift = (c / n_ctx) / ((self._corpus_df[term] + 1) / (n_all + 1))
            if lift < 1.5:
                continue
            scored.append((lift * math.log1p(c) * (1.3 if len(parts) == 2 else 1.0), term, c, lift))
        scored.sort(reverse=True)
        picked, words_used = [], set()
        for _, term, c, lift in scored:
            # skip a single word already covered by a picked two-word phrase, and vice versa
            if any(term in w.split() or w in term.split() for w in words_used):
                continue
            picked.append({"term": term, "count": c, "lift": round(lift, 1)})
            words_used.add(term)
            if len(picked) >= limit:
                break
        return picked

    @staticmethod
    def sentiment(texts: list[str]) -> dict:
        pos = neg = neu = 0
        for t in texts:
            p = sum(bool(r.search(t)) for r in _POS)
            n = sum(bool(r.search(t)) for r in _NEG)
            if p > n:
                pos += 1
            elif n > p:
                neg += 1
            else:
                neu += 1
        total = max(pos + neg + neu, 1)
        return {"positive": round(pos / total, 3), "neutral": round(neu / total, 3),
                "negative": round(neg / total, 3), "n": pos + neg + neu}

    def quotes(self, product: dict, ctx: dict[int, str], limit: int = 3) -> list[dict]:
        ids = sorted(ctx, key=lambda i: int(self.docs[i].get("score") or 0), reverse=True)
        out, seen_threads = [], set()
        for i in ids:
            d = self.docs[i]
            th = d.get("thread") or d["id"]
            if th in seen_threads:
                continue
            raw = re.sub(r"\s+", " ", _URL.sub("", d.get("text") or "")).strip()
            low = raw.lower()
            pos = low.find(product["tokens"][0])
            start = max(0, pos - 80) if pos > 120 else 0
            snippet = raw[start:start + 260].strip()
            if len(snippet) < 25:
                continue
            if start > 0:
                snippet = "…" + snippet
            if start + 260 < len(raw):
                snippet += "…"
            out.append({"text": snippet, "url": d.get("url"), "score": int(d.get("score") or 0),
                        "sub": d.get("sub"), "kind": d.get("kind")})
            seen_threads.add(th)
            if len(out) >= limit:
                break
        return out

    def describe(self, product: dict) -> dict:
        ctx = self.contexts(product)
        # drop the product's own name so "Zero Pore Pads" doesn't count as "pores"
        name = " ".join(product["tokens"])
        texts = [t.replace(name, " ") for t in ctx.values()]
        groups = self.keyword_groups(texts)
        subs = Counter(self.docs[i].get("sub") for i in product["_docs"])
        return {
            "keywords": {**groups, "trending_alongside": self.trending_alongside(product, texts)},
            "sentiment": self.sentiment(texts),
            "quotes": self.quotes(product, ctx),
            "subreddits": dict(subs.most_common(5)),
        }

    # ---------- week-level keyword counts ----------
    def keyword_counts(self) -> dict[str, dict[str, int]]:
        out = {}
        for group, labels in _GROUPS.items():
            c = Counter()
            for d in self.docs:
                for label, pats in labels.items():
                    if any(p.search(d["_clean"]) for p in pats):
                        c[label] += 1
            out[group] = dict(c)
        return out

    def term_counts(self, limit: int = 800) -> dict[str, int]:
        # two-word phrases only: single words are too noisy to call a trend
        bigrams = {t: c for t, c in self._corpus_df.items() if " " in t and c >= 3}
        return dict(Counter(bigrams).most_common(limit))
