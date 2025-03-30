from .constants import LANGUAGE_MAP

def is_positive(value: int) -> int: 
    if value <= 1:
        raise ValueError("{} is not a valid integer".format(value))
    return value

def valid_sentiment_label(sentiment: str) -> str:
    sentimentLabels = {"positive", "neutral", "negative"}
    sentiment = sentiment.strip().lower()
    if sentiment not in sentimentLabels:
        sentiment = "neutral"
    return sentiment.capitalize()

def get_language_label(languageCode: str) -> str:
    languageCode = languageCode.strip().lower()
    return LANGUAGE_MAP.get(languageCode, "Unknown")