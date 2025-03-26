import os
from typing import Dict, List, Tuple
from azure.search.documents.aio import SearchClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from aiocache import cached

from schemas.dashboard import DashboardData, PopularTweet

credential = DefaultAzureCredential()
keyvault_uri = os.environ["KEY_VAULT_URI"]
keyvault_client = SecretClient(vault_url=keyvault_uri, credential=credential)

search_endpoint = keyvault_client.get_secret("SEARCH_ENDPOINT").value
search_key = keyvault_client.get_secret("SEARCH_KEY").value

search_client = SearchClient(endpoint=search_endpoint, 
                                credential=AzureKeyCredential(search_key))


@cached()
async def query_dashboard_data(start_date: str, end_date: str) -> DashboardData:

    filter_query = "linked_entities/any(e: e eq \"CDC\") and \
        created_at gt {}T00:00:00Z and created_at lt {}T23:59:59Z".format(
        start_date, end_date
    )

    results = search_client.search(
        filter=filter_query, 
        top=1000,
        select=[
            "text", "created_at", "source_url", "language", "sentiment",
            "linked_entities", "linked_entity_urls" "keyPhrases", "popularity_score"
        ]
    )

    language_counts: Dict[str, int] = {}
    sentiment_counts: Dict[str, int] = {"positive": 0, "neutral": 0, 
                                        "negative": 0}
    volume_by_date: Dict[str, int] = {}
    entity_counts: Dict[Tuple[str, str], int] = {}
    phrase_counts: Dict[str, int] = {}
    popular_tweets: List[PopularTweet] = []

    async for tweet in results:
        language = tweet.get("language", "unknown")
        language_counts[language] = language_counts.get(language, 0) + 1

        sentiment = tweet.get("sentiment", "unknown")
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        # if sentiment not in ("positive", "neutral", "negative"):
        #     sentiment = "neutral"
        #     missing_sentiment_count += 1

        # sentiment_counts[sentiment] += 1
        tweet_date = tweet["created_at"].date().isoformat()
        volume_by_date[tweet_date] = volume_by_date.get(tweet_date, 0) + 1

        entities = tweet.get("linked_entities", [])
        entity_urls = tweet.get("linked_entity_urls", [])

        for entity, url in zip(entities, entity_urls):
            key = (entity, url)
            entity_counts[key] = entity_counts.get(key, 0) + 1

        for phrase in tweet.get("keyPhrases", []):
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        popular_tweets.append(PopularTweet(
            text = tweet["text"], 
            created_at = tweet["created_at"].date(),
            popularity_score = tweet.get("popularity_score", 0.0),
            source_url = tweet["source_url"]
        ))

        num_entities = 10
        num_phrases = 10
        num_tweets = 5

        # Get list of tuples for view
        top_n_entities = sorted(iterable=entity_counts.items(), 
                                key=lambda x: x[1], reverse=True)[:num_entities]
        top_n_phrases = sorted(iterable=phrase_counts.items(), 
                                key=lambda x: x[1], reverse=True)[:num_phrases]
        top_n_tweets = sorted(iterable=popular_tweets, 
                                key=lambda x: x.popularity_score, 
                                reverse=True)[:num_tweets]
        
        return DashboardData(
            language = language_counts,
            sentiment = sentiment_counts,
            volume = volume_by_date, 
            entities = top_n_entities, 
            key_phrases = top_n_phrases, 
            popular_tweets = top_n_tweets
        )




