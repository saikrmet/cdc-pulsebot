from .validators import is_positive, valid_sentiment_label, get_language_label

from typing import Annotated
from pydantic import AfterValidator, Field

PositiveCount = Annotated[int, Field(gt=0)]
SentimentLabel = Annotated[str, AfterValidator(valid_sentiment_label)]
SentimentScore = Annotated[float, Field(gt=0)]
LanguageLabel = Annotated[str, AfterValidator(get_language_label)]