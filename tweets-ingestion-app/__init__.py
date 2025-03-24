import os
import json
import logging
from datetime import datetime, timedelta, timezone
import azure.functions as func

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import tweepy
from chunking import chunk_text, generate_chunk_id


def main(dailytimer: func.TimerRequest) -> None:
    """Function that pulls tweets about the Centers for Disease Control 
    and Prevention (CDC), format for AI Search index, and push to blob storage.

    Parameters:
        - dailytimer: trigger that defines how often to run function app

    Returns:
        - None
    """
    logging.info("Started CDC Tweets Ingestion Function App")

    credential = DefaultAzureCredential()

    keyvault_uri = os.environ["KEY_VAULT_URI"]
    keyvault_client = SecretClient(vault_url=keyvault_uri, 
                                   credential=credential)

    twitter_token = keyvault_client.get_secret("TWITTER-BEARER-TOKEN").value
    twitter_client = tweepy.Client(bearer_token=twitter_token)

    # Logic for current day 
    now = datetime.now()
    start_time = now - timedelta(1)
    end_time = now

    # Variables for number of tweets per page and number of pages
    max_results = 10
    num_pages = 1

    paginator = tweepy.Paginator(
        twitter_client.search_recent_tweets,
        query="CDC -is:retweet lang:en",
        tweet_fields=["id", "text", "created_at", "author_id", "entities", 
                      "conversation_id", "public_metrics"], 
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(), 
        max_results=max_results
    )

    all_tweets = []
    for page in paginator:
        if not page.data:
            continue
        all_tweets.extend(page.data)

        # Ensures we do not surpass tweet limit
        if len(all_tweets) >= (max_results * num_pages):
            break

    logging.info("Pulled {} on {}.".format(len(all_tweets), 
                                           now.strftime("%B %d, %Y")))

    # Creates sorted list of all_tweets by score_tweet() and gets top 100
    scored_all_tweets = sorted(iterable=all_tweets, key=score_tweet, 
                               reverse=True) 
    top_tweets = scored_all_tweets[:100]  

    # # For future enrichment 
    # hashtags_cleaned = []
    # media_urls_cleaned = []
    # entities = getattr(tweet, "entities", None)
    # if entities is not None:
    #     hashtags = getattr(entities, "hashtags", None)
    #     if hashtags is not None:
    #         # Get value of hashtag text object
    #         for h in hashtags:
    #             hashtags_cleaned.append(h.get("text"))
        
    #     media = getattr(entities, "media", None)
    #     if media is not None:
    #         for m in media:
    #             if m.get("type") == "photo":
    #                 media_urls_cleaned.append(m.get("media_url"))

    chunks = []
    for tweet in top_tweets:
        tweet_id = getattr(tweet, "id", None)
        if tweet_id is None:
            continue

        tweet_text = getattr(tweet, "text", None)
        if tweet_text is None:
            continue
        chunking_result = chunk_text(text=tweet.text, chunk_size=512,
                                           chunk_overlap=50, 
                                           encoding_model="text-embedding-ada-002")

        for i, chunked_text in enumerate(chunking_result):
            chunks.append(
                {
                    "id": generate_chunk_id(id=tweet_id, text=chunked_text),
                    "text": chunked_text,
                    "chunk_index": i,
                    "created_at": tweet.created_at.isoformat(),
                    "author_id": tweet.author_id,
                    "conversation_id": getattr(tweet, "conversation_id", None),
                    "source_url": f"https://twitter.com/i/web/status/{tweet.id}",
                    "popularity_score": score_tweet(tweet),
                    "ingestion_date": now.date().isoformat()
                    # "hashtags": hashtags_cleaned,
                    # "media_urls": media_urls_cleaned
                }
            )

    blob_url = keyvault_client.get_secret("BLOB_URL").value
    blob_container = keyvault_client.get_secret("BLOB_CONTAINER_NAME").value
    blob_path = "{}/cdc-chunks.json".format(now.date())

    blob_service = BlobServiceClient(account_url=blob_url, credential=credential)

    blob_client = blob_service.get_blob_client(container=blob_container, 
                                               blob=blob_path)
    blob_client.upload_blob(json.dumps(obj=chunks, indent=2), overwrite=True)

    logging.info("Added {} chunks at path {}".format(len(chunks), blob_path))


def score_tweet(tweet) -> int:
    """Function that calculates a tweet's popularity score using public 
    metrics of the tweet.

    Parameters:
        - tweet: the tweet object returned by twitter_client

    Returns:
        - int: popularity score or 0 if public_metrics does not exist
    """
    metrics = getattr(tweet, "public_metrics")

    # Metrics doesn't exist, default to score of 0
    if metrics is None:
        return 0

    score = metrics.get("like_count", 0) * 0.5 \
        + metrics.get("retweet_count", 0) * 1.0 \
        + metrics.get("quote_count", 0) * 0.3 \
        + metrics.get("reply_count", 0) * 0.2
    return score