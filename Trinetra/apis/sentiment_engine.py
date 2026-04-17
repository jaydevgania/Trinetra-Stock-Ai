# ============================================================
#  sentiment_engine.py — FinBERT News Sentiment Scoring
#  Model: ProsusAI/finbert (trained on financial news)
# ============================================================

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
import torch

# ── Load FinBERT Model (downloads once, cached after) ────────
print("⏳ Loading FinBERT model... (first run takes 1-2 mins)")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model     = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=0 if torch.cuda.is_available() else -1
)
print("✅ FinBERT loaded!")

# ════════════════════════════════════════════════════════════
#  Score a Single Headline
# ════════════════════════════════════════════════════════════

def score_headline(text):
    """
    Returns sentiment for one headline
    Output: {'label': 'positive'/'negative'/'neutral', 'score': 0.95}
    """
    try:
        text   = text[:512]   # FinBERT max length
        result = sentiment_pipeline(text)[0]
        label  = result['label'].lower()
        score  = round(result['score'], 4)

        emoji = "🟢" if label == "positive" else "🔴" if label == "negative" else "🟡"
        return {"label": label, "score": score, "emoji": emoji, "text": text}
    except Exception as e:
        return {"label": "neutral", "score": 0.5, "emoji": "🟡", "text": text}

# ════════════════════════════════════════════════════════════
#  Score All Headlines from News CSV
# ════════════════════════════════════════════════════════════

def score_all_news(news_df=None, csv_path="data/latest_news.csv"):
    """
    Score all headlines from the news fetcher
    Returns dataframe with sentiment scores added
    """
    try:
        if news_df is None:
            news_df = pd.read_csv(csv_path)

        print(f"\n🤖 Scoring {len(news_df)} headlines with FinBERT...")
        results = []

        for _, row in news_df.iterrows():
            title   = str(row.get('title', ''))
            summary = str(row.get('summary', ''))
            text    = f"{title}. {summary}"[:512]
            scored  = score_headline(text)
            results.append({
                'title':     title,
                'source':    row.get('source', ''),
                'sentiment': scored['label'],
                'confidence':scored['score'],
                'emoji':     scored['emoji'],
            })

        df = pd.DataFrame(results)
        df.to_csv("data/news_sentiment.csv", index=False)
        print(f"✅ Sentiment scoring complete!")
        return df

    except Exception as e:
        print(f"❌ Sentiment error: {e}")
        return None

# ════════════════════════════════════════════════════════════
#  Calculate Overall Market Sentiment Score
# ════════════════════════════════════════════════════════════

def get_market_sentiment_score(df=None):
    """
    Aggregates all headlines into one market sentiment score

    Score > 0.6   = Bullish market sentiment
    Score 0.4-0.6 = Neutral
    Score < 0.4   = Bearish market sentiment
    """
    if df is None:
        try:
            df = pd.read_csv("data/news_sentiment.csv")
        except:
            print("❌ No sentiment data found. Run score_all_news() first.")
            return None

    total     = len(df)
    positive  = len(df[df['sentiment'] == 'positive'])
    negative  = len(df[df['sentiment'] == 'negative'])
    neutral   = len(df[df['sentiment'] == 'neutral'])

    # Weighted score (positive=1, neutral=0.5, negative=0)
    score = round((positive * 1.0 + neutral * 0.5) / total, 2)

    if score > 0.6:
        overall = "🟢 BULLISH — Good news dominates"
    elif score < 0.4:
        overall = "🔴 BEARISH — Bad news dominates"
    else:
        overall = "🟡 NEUTRAL — Mixed signals"

    print(f"\n📊 MARKET SENTIMENT REPORT")
    print(f"=" * 40)
    print(f"  Total headlines : {total}")
    print(f"  🟢 Positive     : {positive} ({round(positive/total*100)}%)")
    print(f"  🟡 Neutral      : {neutral}  ({round(neutral/total*100)}%)")
    print(f"  🔴 Negative     : {negative} ({round(negative/total*100)}%)")
    print(f"  Sentiment Score : {score}/1.0")
    print(f"  Overall         : {overall}")
    print(f"=" * 40)

    return {
        "score":    score,
        "overall":  overall,
        "positive": positive,
        "negative": negative,
        "neutral":  neutral,
        "total":    total
    }

# ════════════════════════════════════════════════════════════
#  Top Bullish & Bearish Headlines
# ════════════════════════════════════════════════════════════

def get_top_headlines(df=None, n=5):
    """Show most bullish and most bearish headlines"""
    if df is None:
        try:
            df = pd.read_csv("data/news_sentiment.csv")
        except:
            return

    print(f"\n🟢 TOP {n} BULLISH HEADLINES:")
    bullish = df[df['sentiment'] == 'positive'].nlargest(n, 'confidence')
    for _, row in bullish.iterrows():
        print(f"  ✅ [{row['source']}] {row['title'][:80]}")

    print(f"\n🔴 TOP {n} BEARISH HEADLINES:")
    bearish = df[df['sentiment'] == 'negative'].nlargest(n, 'confidence')
    for _, row in bearish.iterrows():
        print(f"  ❌ [{row['source']}] {row['title'][:80]}")

# ── Main Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with sample headlines
    test_headlines = [
        "Nifty surges 200 points as FIIs pour money into Indian markets",
        "RBI keeps interest rates unchanged, market reacts positively",
        "Global recession fears drag Indian indices lower",
        "Sensex crashes 500 points amid weak global cues",
        "IT stocks rally as rupee weakens against dollar",
    ]

    print("🧪 Testing FinBERT on sample headlines:\n")
    for headline in test_headlines:
        result = score_headline(headline)
        print(f"  {result['emoji']} [{result['label'].upper()} {result['score']}] {headline[:60]}")

    print("\n📂 To score all your news, run:")
    print("  from apis.news_fetcher import get_all_news")
    print("  news_df = get_all_news()")
    print("  scored_df = score_all_news(news_df)")
    print("  get_market_sentiment_score(scored_df)")