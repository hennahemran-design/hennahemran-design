# Beauty Trend Tracker

A website that shows the **top 5 trending skincare and makeup products each week**, and the keywords that come up with them: what people recommend each product for, what they like, what they complain about, and what they search on Google next to its name. You can go back to any past week, or look up a product or keyword to see how it moved week by week.

## What you see

- **Skincare / Makeup tabs.** The 5 products with the most buzz this week, weighted toward products that are growing. Each card shows:
  - **Recommended for**: skin types and concerns people mention with it (dry skin, acne, hyperpigmentation, hooded eyes…)
  - **What people like**: lightweight, no white cast, long-lasting, holy grail, great dupe…
  - **Trending alongside it**: words and phrases that come up far more often next to this product than in other posts
  - **Google searches**: Google's autocomplete suggestions for the product name (for example "… for acne" or "… vs …"), newest week only
  - **Complaints** and the **tone** of mentions (positive, neutral or negative)
  - A sparkline of its buzz over the last 9 weeks, the change against its 4-week average, and quotes that link to the threads
- **Trending keywords.** Skin needs, praise and complaints that are rising across all posts, plus new two-word phrases (a new technique or trend name, for example).
- **Look up past weeks.** Search a product, brand or keyword to get a weekly chart and table, and see every week's top 5 at a glance.
- **Climbing on Amazon.** When Amazon allows it, the newest week also lists Amazon's Movers & Shakers in Skin Care and Makeup.

## Where the data comes from

| Source | What it gives | Weeks |
|---|---|---|
| [Arctic Shift](https://arctic-shift.photon-reddit.com) Reddit archive | Posts and comments from r/SkincareAddiction, r/AsianBeauty, r/30PlusSkinCare, r/SkincareAddicts, r/MakeupAddiction, r/drugstoreMUA, r/MakeupRehab, r/BeautyGuruChatter, r/Sephora and r/Ulta | Any week, so past weeks can be filled in |
| [Bluesky](https://bsky.app) search | Popular posts about skincare, makeup, sunscreen, foundation, blush and similar | Any week |
| reddit.com (optional) | The newest days, if you add Reddit API keys (see Setup) | Last ~9 days |
| Google autocomplete | Searches people type next to each product name | Newest week |
| Amazon Movers & Shakers | Products whose sales rank jumped most | Newest week, when Amazon allows it |

**How products are found.** The scraper knows about 200 brands (`scraper/lexicon.py`). When a brand is mentioned, it reads the words after it ("Medicube *Zero Pore Pads*") and keeps the most common spelling. That way it can pick up new products from those brands without a product list.

**How trending is scored.** *Buzz* = separate threads mentioning the product, plus 0.4 for each extra post or comment, plus a small boost for upvotes. The ranking multiplies buzz by its growth against the product's average over the previous 4 weeks, so products that suddenly take off beat products that are always popular. A product needs at least 3 separate threads to rank.

**Limits.** This tracks what beauty Reddit and Bluesky are talking about, which leans toward enthusiasts and isn't a measure of sales. The keyword groups are word lists, so sarcasm and negation ("not lightweight at all") can be miscounted. Product names are only found for brands in the list.

## How it runs

A GitHub Action, `.github/workflows/beauty-trends.yml`, runs every **Monday** (to close out the past week) and **Thursday** (to refresh the week in progress). It:

1. runs the tests,
2. fills in any missing week from the last 6 and rebuilds the current week,
3. commits the results to `data/` (one file per week in `data/weeks/`, plus `data/index.json`),
4. publishes the site to GitHub Pages (from the default branch only).

The site is plain HTML and JavaScript with no build step. It reads those JSON files.

### Setup (once)

1. **Turn on Pages:** Settings → Pages → Source: **GitHub Actions**.
2. **Allow the Action to save data:** Settings → Actions → General → Workflow permissions → **Read and write**.
3. *(Optional)* reddit.com refuses anonymous requests from GitHub's servers, so by default the tracker reads Reddit through the Arctic Shift archive, which can lag by a day or so. To also read reddit.com directly, create a "script" app at <https://www.reddit.com/prefs/apps> and add its id and secret as repository secrets named `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`.

To collect data right away, or to go further back: Actions → **Beauty trend scrape** → **Run workflow**, then set *weeks* (for example `12`).

### Running it on your computer

Install the dependencies:

```bash
pip install -r beauty-trend-tracker/scraper/requirements.txt
```

Fill in the last 6 weeks and the current week:

```bash
python beauty-trend-tracker/scraper/scrape.py --weeks 6
```

Serve the site locally:

```bash
python -m http.server -d beauty-trend-tracker 8000
```

Then open <http://localhost:8000>. Run `scrape.py --help` for the other options, for example `--week 2026-W40 --refresh` to rebuild one week.

### Tuning

All word lists are in `scraper/lexicon.py`:

- `SUBREDDITS`: which communities to read
- `BRANDS`: brands to track (add aliases people use, like `"lrp"`)
- `RECOMMENDED_FOR`, `PEOPLE_LIKE`, `COMPLAINTS`: keyword groups, each a label and the patterns that count toward it

Tests: `python -m pytest beauty-trend-tracker/tests`
