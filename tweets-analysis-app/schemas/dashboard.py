from pydantic import BaseModel
from typing import Dict, List, Tuple
from datetime import date

class PopularTweet(BaseModel):
    text: str
    created_at: date
    popularity_score: float
    source_url: str
    
class DashboardData(BaseModel):
    language: Dict[str, int]
    sentiment: Dict[str, int]
    volume: Dict[str, int]
    entities: List[Tuple[Tuple[str, str], int]]
    key_phrases: List[Tuple[str, int]]
    popular_tweets: List[PopularTweet]

