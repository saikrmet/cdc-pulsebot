from .validators import is_positive, valid_sentiment_label, get_language_label

from typing import Annotated
from pydantic import AfterValidator

PositiveCount = Annotated[int, AfterValidator(is_positive)]
SentimentLabel = Annotated[str, AfterValidator(valid_sentiment_label)]
SentimentScore = Annotated[int, AfterValidator(is_positive)]
LanguageLabel = Annotated[str, AfterValidator(get_language_label)]