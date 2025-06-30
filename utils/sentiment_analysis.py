# utils/sentiment_analysis.py

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize sentiment engine once
analyzer = SentimentIntensityAnalyzer()


def get_yahoo_finance_headlines(ticker):
    """Get top Yahoo Finance headlines for the stock."""
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        results = response.json()
        news_items = results.get("news", [])[:10]  # Top 10 headlines
        headlines = [item['title'] for item in news_items if 'title' in item]
        return headlines
    except Exception as e:
        return []


def analyze_sentiment(headlines):
    """Returns scores and labels for a list of headlines."""
    results = []
    for text in headlines:
        score = analyzer.polarity_scores(text)['compound']
        label = (
            "Positive" if score > 0.2 else
            "Negative" if score < -0.2 else
            "Neutral"
        )
        results.append({"headline": text, "score": round(score, 3), "label": label})
    return results


def summarize_sentiment(results):
    """Summarize overall sentiment score and label."""
    if not results:
        return 0, "Neutral"
    avg = sum([r["score"] for r in results]) / len(results)
    label = (
        "Positive" if avg > 0.2 else
        "Negative" if avg < -0.2 else
        "Neutral"
    )
    return round(avg, 3), label
