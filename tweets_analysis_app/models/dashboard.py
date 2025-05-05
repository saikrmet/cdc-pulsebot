from pydantic import BaseModel
from typing import Dict, List, Tuple
from tweets_analysis_app.types.annotated import PositiveCount, SentimentLabel, SentimentScore, \
    LanguageLabel, DatetimeString
from datetime import datetime



    
# Model for count by datetime
class DateCountObj(BaseModel):
    date: DatetimeString
    count: PositiveCount

# Model for count by sentiment label
class SentimentLabelCountObj(BaseModel):
    label: SentimentLabel
    count: PositiveCount

# Model for sentiment score by date
class DateSentimentScoreObj(BaseModel):
    date: DatetimeString
    score: SentimentScore

# Model for count by language
class LanguageCountObj(BaseModel):
    language: LanguageLabel
    count: PositiveCount

# # Model for count by keyword
# class KeywordCountObj(BaseModel):
#     keyword: str
#     count: PositiveCount

# # Model for input to GenAI consolidation
# class RawKeywordsObj(BaseModel):
#     data: List[KeywordCountObj]

# class CleanKeywordsObj(BaseModel):
#     data: List[KeywordCountObj]

# Model for count by linked entity
class EntityCountObj(BaseModel):
    name: str
    url: str
    count: int

# Model for popular tweets
class PopularTweet(BaseModel):
    text: str
    created_at: DatetimeString
    username: str
    source_url: str
    language: LanguageLabel
    like_count: int
    retweet_count: int
    quote_count: int
    reply_count: int

    @property
    def formatted_created_at(self) -> str:
        return datetime.strptime(self.created_at, "%Y-%m-%d").strftime("%m/%d/%Y")

    def dict(self, *args, **kwargs):
        # Override the dict method to include the formatted_created_at
        data = super().dict(*args, **kwargs)
        data["formatted_created_at"] = self.formatted_created_at
        return data

class DashboardData(BaseModel):
    date_counts: List[DateCountObj]
    sentiment_label_counts: List[SentimentLabelCountObj]
    date_sentiment_scores: List[DateSentimentScoreObj]
    language_counts: List[LanguageCountObj]
    entity_counts: List[EntityCountObj]
    # keyword_counts: CleanKeywordsObj
    popular_tweets: List[PopularTweet]




