from datetime import datetime
from tweets_analysis_app.types.constants import LANGUAGE_MAP


def consolidate_sentiment_label(sentiment: str) -> str:
    sentimentLabels = {"positive", "neutral", "negative"}
    sentiment = sentiment.strip().lower()
    if sentiment not in sentimentLabels:
        sentiment = "neutral"
    return sentiment.capitalize()

def get_language_label(languageCode: str) -> str:
    languageCode = languageCode.strip().lower()
    return LANGUAGE_MAP.get(languageCode, "Unknown")

def format_datetime(datetimeObj: datetime) -> str:
    return datetimeObj.date().isoformat()