from datetime import datetime
from tweets_analysis_app.types.validators import consolidate_sentiment_label, get_language_label, format_datetime
from typing import Annotated
from pydantic import AfterValidator, Field

DatetimeString = Annotated[datetime, AfterValidator(format_datetime)]
PositiveCount = Annotated[int, Field(gt=0)]
SentimentLabel = Annotated[str, AfterValidator(consolidate_sentiment_label)]
SentimentScore = Annotated[float, Field(gt=0)]
LanguageLabel = Annotated[str, AfterValidator(get_language_label)]