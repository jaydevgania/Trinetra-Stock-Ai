# ============================================================
#  news_fetcher.py — All News Sources (No NewsAPI needed!)
#  Sources: Google RSS + ET + Moneycontrol + LiveMint +
#           Finshots + NDTV Business + GNews (optional)
#  ✅ Zero work email required for any of these
# ============================================================

import feedparser
import requests
import pandas as pd
import os
from datetime import datetime

# ── Optional: GNews (signup with normal Gmail — free 100/day)
GNEWS_API_KEY = "471de4356fb4cbfc54642c7cd7086967"   # get free key at gnews.io
USE_GNEWS     = True   # change to True after getting key


# ════════════════════════════════════════════════════════════
#  1. GOOGLE NEWS RSS — ✅ No signup, completely free
# ════════════════════════════════════════════════════════════

GOOGLE_RSS_FEEDS = {
    "Indian Market":   "https://news.google.com/rss/search?q=Nifty+Sensex+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
    "Bank Nifty":      "https://news.google.com/rss/search?q=Bank+Nifty+options&hl=en-IN&gl=IN&ceid=IN:en",
    "Global Market":   "https://news.google.com/rss/search?q=global+stock+market+economy&hl=en&gl=US&ceid=US:en",
    "Crude Oil":       "https://news.google.com/rss/search?q=crude+oil+price+today&hl=en-IN&gl=IN&ceid=IN:en",
    "US Fed":          "https://news.google.com/rss/search?q=US+Federal+Reserve+interest+rates&hl=en&gl=US&ceid=US:en",
    "Company Results": "https://news.google.com/rss/search?q=NSE+BSE+quarterly+results+earnings&hl=en-IN&gl=IN&ceid=IN:en",
    "RBI Policy":      "https://news.google.com/rss/search?q=RBI+monetary+policy+India&hl=en-IN&gl=IN&ceid=IN:en",
    "FII DII":         "https://news.google.com/rss/search?q=FII+DII+buying+selling+India&hl=en-IN&gl=IN&ceid=IN:en",
}

def get_google_news(feed_name="Indian Market", count=8):
    try:
        feed = feedparser.parse(GOOGLE_RSS_FEEDS[feed_name])
        news = [{
            'source':    'Google News',
            'category':  feed_name,
            'title':     e.title,
            'summary':   e.get('summary', ''),
            'url':       e.link,
            'published': e.get('published', str(datetime.now())),
        } for e in feed.entries[:count]]
        print(f"✅ Google News [{feed_name}]: {len(news)} articles")
        return news
    except Exception as e:
        print(f"❌ Google RSS [{feed_name}]: {e}")
        return []

def get_all_google_news():
    all_news = []
    for feed_name in GOOGLE_RSS_FEEDS:
        all_news.extend(get_google_news(feed_name, count=5))
    return all_news

# ════════════════════════════════════════════════════════════
#  2. ECONOMIC TIMES RSS — ✅ No signup required
# ════════════════════════════════════════════════════════════

ET_FEEDS = {
    "Markets":  "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Stocks":   "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "Economy":  "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "Sensex":   "https://economictimes.indiatimes.com/markets/rssfeeds/70450990.cms",
}

def get_et_news(count=10):
    all_news = []
    for feed_name, url in ET_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:count//4]:
                all_news.append({
                    'source':    'Economic Times',
                    'category':  feed_name,
                    'title':     e.title,
                    'summary':   e.get('summary', ''),
                    'url':       e.link,
                    'published': e.get('published', str(datetime.now())),
                })
        except Exception as e:
            print(f"❌ ET [{feed_name}]: {e}")
    print(f"✅ Economic Times: {len(all_news)} articles")
    return all_news

# ════════════════════════════════════════════════════════════
#  3. LIVEMINT RSS — ✅ No signup required
# ════════════════════════════════════════════════════════════

MINT_FEEDS = {
    "Markets":   "https://www.livemint.com/rss/markets",
    "Economy":   "https://www.livemint.com/rss/economy",
    "Companies": "https://www.livemint.com/rss/companies",
}

def get_livemint_news(count=9):
    all_news = []
    for feed_name, url in MINT_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:count//3]:
                all_news.append({
                    'source':    'LiveMint',
                    'category':  feed_name,
                    'title':     e.title,
                    'summary':   e.get('summary', ''),
                    'url':       e.link,
                    'published': e.get('published', str(datetime.now())),
                })
        except Exception as ex:
            print(f"❌ LiveMint [{feed_name}]: {ex}")
    print(f"✅ LiveMint: {len(all_news)} articles")
    return all_news

# ════════════════════════════════════════════════════════════
#  4. MONEYCONTROL RSS — ✅ No signup required
# ════════════════════════════════════════════════════════════

def get_moneycontrol_news(count=10):
    try:
        feed = feedparser.parse("https://www.moneycontrol.com/rss/marketreports.xml")
        news = [{
            'source':    'Moneycontrol',
            'category':  'Markets',
            'title':     e.title,
            'summary':   e.get('summary', ''),
            'url':       e.link,
            'published': e.get('published', str(datetime.now())),
        } for e in feed.entries[:count]]
        print(f"✅ Moneycontrol: {len(news)} articles")
        return news
    except Exception as e:
        print(f"❌ Moneycontrol: {e}")
        return []

# ════════════════════════════════════════════════════════════
#  5. NDTV BUSINESS RSS — ✅ No signup required
# ════════════════════════════════════════════════════════════

def get_ndtv_business_news(count=8):
    try:
        feed = feedparser.parse("https://feeds.feedburner.com/ndtvprofit-latest")
        news = [{
            'source':    'NDTV Business',
            'category':  'Business',
            'title':     e.title,
            'summary':   e.get('summary', ''),
            'url':       e.link,
            'published': e.get('published', str(datetime.now())),
        } for e in feed.entries[:count]]
        print(f"✅ NDTV Business: {len(news)} articles")
        return news
    except Exception as e:
        print(f"❌ NDTV Business: {e}")
        return []

# ════════════════════════════════════════════════════════════
#  6. FINSHOTS RSS — ✅ No signup required
# ════════════════════════════════════════════════════════════

def get_finshots_news(count=5):
    try:
        feed = feedparser.parse("https://finshots.in/feed")
        news = [{
            'source':    'Finshots',
            'category':  'Finance',
            'title':     e.title,
            'summary':   e.get('summary', ''),
            'url':       e.link,
            'published': e.get('published', str(datetime.now())),
        } for e in feed.entries[:count]]
        print(f"✅ Finshots: {len(news)} articles")
        return news
    except Exception as e:
        print(f"❌ Finshots: {e}")
        return []

# ════════════════════════════════════════════════════════════
#  7. GNEWS API — Optional (Gmail signup works, free 100/day)
#     👉 Sign up at https://gnews.io using your Gmail
# ════════════════════════════════════════════════════════════

def get_gnews(query="Nifty Sensex India stock market", count=10):
    if not USE_GNEWS or GNEWS_API_KEY == "your_gnews_key_here":
        return []
    try:
        url  = f"https://gnews.io/api/v4/search?q={query}&lang=en&country=in&max={count}&apikey={GNEWS_API_KEY}"
        resp = requests.get(url, timeout=10).json()
        news = [{
            'source':    a['source']['name'],
            'category':  'GNews',
            'title':     a['title'],
            'summary':   a.get('description', ''),
            'url':       a['url'],
            'published': a['publishedAt'],
        } for a in resp.get('articles', [])]
        print(f"✅ GNews: {len(news)} articles")
        return news
    except Exception as e:
        print(f"❌ GNews: {e}")
        return []

# ════════════════════════════════════════════════════════════
#  MASTER — Fetch ALL News From ALL Sources
# ════════════════════════════════════════════════════════════

def get_all_news():
    print("\n📰 Trinetra — Fetching live news...")
    print("=" * 55)

    all_news = []
    all_news.extend(get_all_google_news())       # ~40 articles
    all_news.extend(get_et_news())               # ~10 articles
    all_news.extend(get_livemint_news())         # ~9 articles
    all_news.extend(get_moneycontrol_news())     # ~10 articles
    all_news.extend(get_ndtv_business_news())    # ~8 articles
    all_news.extend(get_finshots_news())         # ~5 articles
    all_news.extend(get_gnews())                 # ~10 (if enabled)

    # Create data folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Clean
    df = pd.DataFrame(all_news)
    df = df.drop_duplicates(subset=['title'])
    df = df[df['title'].str.len() > 10]
    df = df.reset_index(drop=True)
    df.to_csv("data/latest_news.csv", index=False)

    print(f"\n✅ Total unique articles : {len(df)}")
    print("=" * 55)
    return df

# ── Main Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    df = get_all_news()
    print(f"\n📰 Sample Headlines:")
    for _, row in df.head(10).iterrows():
        print(f"  [{row['source']:15}] {row['title'][:70]}")