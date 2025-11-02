import requests
import pandas as pd
from datetime import datetime
from transformers import pipeline, BertTokenizer, BertForSequenceClassification

POLYGON_API_KEY = "Xfls6mGPBAT1aRAXMrpWs7vdiXUbSUv4"
MODEL_NAME = "ProsusAI/finbert"

tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
model = BertForSequenceClassification.from_pretrained(MODEL_NAME)
sentiment_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)


def get_stock_sentiments(ticker: str):
    """Fetch and analyze latest news for given ticker."""
    url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&apiKey={POLYGON_API_KEY}"
    response = requests.get(url)
    articles = response.json().get("results", []) if response.ok else []

    data = []
    for article in articles[:10]:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        label = sentiment_pipeline(text)[0]["label"]
        score = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}.get(label, 0)
        data.append({"date": datetime.now().date(), "headline": article.get("title", ""), "sentiment": label, "score": score})

    return pd.DataFrame(data)