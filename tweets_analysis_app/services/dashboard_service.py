import os
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
from azure.search.documents.aio import AsyncSearchItemPaged

from aiocache import cached

from tweets_analysis_app.clients import get_azure_clients
from tweets_analysis_app.models.dashboard import DashboardData, PopularTweet, DateCountObj, SentimentLabelCountObj, LanguageCountObj, DateSentimentScoreObj, EntityCountObj
from tweets_analysis_app.types.validators import consolidate_sentiment_label
import logging

logger = logging.getLogger(__name__)


# vector_prompt = "Tweets related to the U.S. Centers for Disease Control and Prevention (CDC) also known as the Centers for Disease Control, which is the national public health agency of the United States and a key part of the federal government. These tweets may describe or refer to the CDC's activities, policies, decisions, leadership, public communications, health alerts, funding actions, regulatory guidance, reports, or institutional role in managing and responding to public health matters. The content may be factual, opinionated, political, supportive, or critical in tone. Tweets can involve the CDC taking action (e.g., issuing guidance, retracting statements, canceling programs, releasing research), being discussed in the news or media, being cited in connection with public health debates, or being evaluated by the public or political figures. Tweets might use headlines like 'CDC warns…', 'CDC confirms…', 'CDC cancels…', or casual phrases such as 'The CDC is a joke', 'Trust the CDC', 'CDC dropped the ball', or 'According to the CDC…'. They may also reference major figures or entities associated with the CDC (e.g., its director, U.S. presidents, Congress, NIH, FDA, or WHO) or touch on issues such as data transparency, disease outbreaks, vaccine recommendations, public trust, misinformation, state vs. federal guidance, or health equity. Tweets may include controversy, praise, policy reactions, or emotional opinions about the agency. They may reflect events like pandemic response, new disease variants, political conflict over health policy, public trust in science, or CDC interactions with other governmental or global institutions. All tweets must treat the CDC as the primary subject or actor in a governmental or health-related context. The query excludes tweets where 'CDC' is used incidentally, in usernames or tags (e.g., @cdc_gocats, #CDC), or in reference to unrelated organizations or technical terms such as Apache CDC or Change Data Capture. Tweets where 'CDC' is mentioned only in passing, used as a generic acronym, or not semantically related to the U.S. government health agency should be ignored. The agency's main goal is the protection of public health and safety through the control and prevention of disease, injury, and disability in the US and worldwide. It especially focuses its attention on infectious disease, food borne pathogens, environmental health, occupational safety and health, health promotion, injury prevention. The CDC also conducts research and provides information on non-infectious diseases, such as obesity and diabetes."
# search_threshold = 0.58
search_query = "Centers for Disease Control and Prevention^10 OR (CDC AND (vaccine OR disease OR outbreak OR infection OR 'public health' OR COVID OR advisory OR confirmed OR director))^5"
search_query_alt = "((Centers for Disease Control and Prevention)^10 OR (CDC AND (COVID OR vaccine OR outbreak OR confirmed OR public health OR disease OR funding OR director OR alert OR cases OR advisory OR TB OR nominate OR lead OR picks OR US OR USA OR nurses OR pharmacists OR delegates OR leadership OR documents))) AND NOT (Africa CDC OR CDC_TB OR CDC_Europe OR CDC_Upland OR Vehicle Technician OR job alert OR @CDC_Zimbabwe OR @LoadedLions_CDC)"
search_threshold = 3.0


@cached()
async def get_dashboard_data(start_date: str, end_date: str) -> DashboardData:
    clients = get_azure_clients()
    search_client = clients.search_client

    filter_query = "created_at gt {}T00:00:00Z and created_at lt {}T23:59:59Z".format(start_date, end_date)

    dashboard_results = await search_client.search(
        search_text=search_query, 
        filter=filter_query,
        facets=["created_at,interval:day", "sentiment", "language", "linked_entities"], 
        top=1000,
        select=["created_at", "sentiment", "language", "keyPhrases", "linked_entities", "linked_entity_urls"]
    )

    popular_results = await search_client.search(
        search_text=search_query,
        filter=filter_query,
        top=25,
        select=["text", "created_at", "username", "source_url", "like_count", "retweet_count", "quote_count", "reply_count", "language"]
    )

    filtered_dashboard_results, date_counts, sentiment_label_counts, language_counts, entity_counts = \
        await filter_dashboard_results(results=dashboard_results, threshold=search_threshold)

    filtered_popular_results = await filter_popular_results(results=popular_results, threshold=search_threshold, top=5)
    sorted_popular_results = sort_filtered_results_by_metrics(filtered_popular_results)

    date_sentiment_scores = calculate_date_sentiment_scores(filtered_dashboard_results)

    # print("Date Counts: []" + "".join(str(date_counts)) + "]")
    # print("Sentiment Label Counts: []" + "".join(str(sentiment_label_counts)) + "]")
    # print("Date Sentiment Score: []" + "".join(str(date_sentiment_scores)) + "]")
    # print("Language Counts: []" + "".join(str(language_counts)) + "]")
    # print("Entity Counts: []" + "".join(str(entity_counts)) + "]")
    # print("Popular Tweets: []" + "".join(str(filtered_popular_results)) + "]")

    return DashboardData(
        date_counts=date_counts, 
        sentiment_label_counts=sentiment_label_counts, 
        date_sentiment_scores=date_sentiment_scores,
        language_counts=language_counts,
        entity_counts=entity_counts,
        popular_tweets=sorted_popular_results
    )

    
async def filter_popular_results(results: AsyncSearchItemPaged[Dict], threshold: int, top: int) -> List[PopularTweet]:
    filtered_results = []
    i = 0
    async for result in results:
        if i == top:
            break
        score = result.get("@search.score", 0)
        if score >= threshold:
            filtered_results.append(PopularTweet(
                text=result.get("text", None), 
                created_at=result.get("created_at", None), 
                username=result.get("username", None), 
                source_url=result.get("source_url", None),
                language=result.get("language", None), 
                like_count=result.get("like_count", None),
                retweet_count=result.get("retweet_count", None),
                quote_count=result.get("quote_count", None),
                reply_count=result.get("reply_count", None)
            ))
            i += 1
    
    return filtered_results


async def filter_dashboard_results(
        results: AsyncSearchItemPaged[Dict], threshold: int) -> Tuple[List[dict],
             List[DateCountObj], List[SentimentLabelCountObj], List[LanguageCountObj], List[EntityCountObj]]:
    original_facets = await results.get_facets()

    filtered_results = []
    # Nested dictionary generator
    subtract_facets = defaultdict(lambda: defaultdict(int))
    entity_url_map = defaultdict()

    async for result in results:
        score = result.get("@search.score", 0)
        if score >= threshold:
            filtered_results.append(result)
            linked_entities = result.get("linked_entities", None)
            linked_entity_urls = result.get("linked_entity_urls", None)

            # Create a map of entity to url for valid CDC tweets
            for entity, url in zip(linked_entities, linked_entity_urls):
                if entity not in entity_url_map:
                    entity_url_map[entity] = url
        else:
            for facet_type in original_facets.keys():
                facet_value = result.get(facet_type, None)
                if facet_value is not None:
                    if isinstance(facet_value, str):
                        if facet_type == "created_at":
                            facet_value = datetime.fromisoformat(facet_value.replace("Z", ""))\
                                            .replace(hour=0, minute=0, second=0, microsecond=0)
                        subtract_facets[facet_type][facet_value] += 1
                    elif isinstance(facet_value, list):
                        for item in facet_value:
                            subtract_facets[facet_type][item] += 1
    
    date_counts: List[DateCountObj] = []
    sentiment_label_counts_map = defaultdict(int)
    language_counts: List[LanguageCountObj] = []
    entity_counts: List[EntityCountObj] = []
    for facet_type in original_facets.keys():
        for facet_obj in original_facets.get(facet_type):
            value = facet_obj["value"]
            old_count = facet_obj["count"]
            if facet_type == "created_at":
                value = datetime.fromisoformat(value.replace("Z", ""))\
                            .replace(hour=0, minute=0, second=0, microsecond=0)
            subtract_count = subtract_facets[facet_type].get(value, 0)
            new_count = max(old_count - subtract_count, 0)
            if new_count == 0:
                continue

            if facet_type == "created_at":
                date_counts.append(DateCountObj(date=value, count=new_count))
            elif facet_type == "sentiment":
                sentiment_label_counts_map[consolidate_sentiment_label(value)] += new_count
            elif facet_type == "language":
                language_counts.append(LanguageCountObj(language=value, count=new_count))
            elif facet_type == "linked_entities":
                url = entity_url_map.get(value)
                entity_counts.append(EntityCountObj(name=value, url=url, count=new_count))

    sentiment_label_counts = [SentimentLabelCountObj(label=label, count=count) for label, count in sentiment_label_counts_map.items()]
    order = ["Positive", "Neutral", "Negative"]
    sentiment_label_counts.sort(key=lambda x: order.index(x.label))
        
    return filtered_results, date_counts, sentiment_label_counts, language_counts, entity_counts


def calculate_date_sentiment_scores(results: List[dict]) -> List[DateSentimentScoreObj]:
    date_sentiment_scores: List[DateSentimentScoreObj] = []
    sentiment_map = {"positive": 1.0, "neutral": 0.5, "negative": 0}
    date_sentiment_map = defaultdict(list)
    for result in results:
        raw_datetime = result.get("created_at", None)
        date = datetime.fromisoformat(raw_datetime.replace("Z", ""))\
                    .replace(hour=0, minute=0, second=0, microsecond=0)
        
        sentiment = result.get("sentiment", None)
        if sentiment not in sentiment_map:
            sentiment = "neutral"

        date_sentiment_map[date].append(sentiment_map.get(sentiment))

    for date, score_list in date_sentiment_map.items():
        score_avg = sum(score_list) / len(score_list)
        date_sentiment_scores.append(DateSentimentScoreObj(date=date, score=score_avg))
    
    date_sentiment_scores.sort(key=lambda x: datetime.fromisoformat(x.date))

    return date_sentiment_scores


def sort_filtered_results_by_metrics(filtered_results: List[PopularTweet]) -> List[PopularTweet]:
    """
    Sorts the filtered results list using a custom scoring metric.

    The score is calculated as:
        score = like_count * 0.5 + retweet_count * 1.0 + quote_count * 0.3 + reply_count * 0.2

    Args:
        filtered_results (List[PopularTweet]): List of PopularTweet objects.

    Returns:
        List[PopularTweet]: Sorted list of PopularTweet objects.
    """
    def calculate_score(tweet: PopularTweet) -> float:
        metrics = {
            "like_count": tweet.like_count or 0,
            "retweet_count": tweet.retweet_count or 0,
            "quote_count": tweet.quote_count or 0,
            "reply_count": tweet.reply_count or 0
        }
        score = metrics.get("like_count", 0) * 0.5 \
            + metrics.get("retweet_count", 0) * 1.0 \
            + metrics.get("quote_count", 0) * 0.3 \
            + metrics.get("reply_count", 0) * 0.2
        return score

    return sorted(filtered_results, key=calculate_score, reverse=True)

# async def consolidate_phrases(results: List[dict]) -> Dict[str, int]:
#     flattened_phrases = []
#     for result in results:
#         flattened_phrases.extend(result.get("keyPhrases", []))


    # OLD CODE FOR PROCESSING
    # logger.info("received search results")

    # cdc_filtered_results = []
    # async for tweet in results:
    #     if tweet.get("@search.score", 0) >= search_threshold:
    #         cdc_filtered_results.append(tweet)

    # logger.info("filtered search results")

    # language_counts: Dict[str, int] = {}
    # sentiment_counts: Dict[str, int] = {"positive": 0, "neutral": 0, 
    #                                     "negative": 0}
    # sentiment_map = {"positive": 1.0, "neutral": 0.5, "negative": 0}
    # sentiment_by_date: Dict[str, List[float]] = {}
    # volume_by_date: Dict[str, int] = {}
    # entity_counts: Dict[Tuple[str, str], int] = {}
    # phrase_counts: Dict[str, int] = {}
    # popular_tweets: List[PopularTweet] = []

    # missing_sentiment_count = 0
    # for tweet in cdc_filtered_results:
    #     language = tweet.get("language", "unknown")
    #     language_counts[language] = language_counts.get(language, 0) + 1

    #     sentiment = tweet.get("sentiment")
    #     if sentiment not in ("positive", "neutral", "negative"):
    #         sentiment = "neutral"
    #         missing_sentiment_count += 1

    #     sentiment_counts[sentiment] += 1

    #     tweet_date = datetime.fromisoformat(tweet["created_at"].replace("Z", "")).date().isoformat()
    #     volume_by_date[tweet_date] = volume_by_date.get(tweet_date, 0) + 1

    #     sentiment_score = sentiment_map.get(sentiment, 0.5)
    #     if tweet_date not in sentiment_by_date:
    #         sentiment_by_date[tweet_date] = []
    #     sentiment_by_date[tweet_date].append(sentiment_score)

    #     entities = tweet.get("linked_entities", [])
    #     entity_urls = tweet.get("linked_entity_urls", [])

    #     for entity, url in zip(entities, entity_urls):
    #         key = (entity, url)
    #         entity_counts[key] = entity_counts.get(key, 0) + 1

    #     for phrase in tweet.get("keyPhrases", []):
    #         phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

    #     popular_tweets.append(PopularTweet(
    #         text = tweet["text"], 
    #         created_at = tweet_date,
    #         popularity_score = tweet.get("popularity_score", 0.0),
    #         source_url = tweet["source_url"]
    #     ))


    # logger.info("finished async processing for dashboard data")
    # num_entities = 10
    # num_phrases = 10
    # num_tweets = 5

    # # Get list of tuples for view
    # top_n_entities_raw = sorted(entity_counts.items(), 
    #                         key=lambda x: x[1], reverse=True)[:num_entities]
    # top_n_phrases = sorted(phrase_counts.items(), 
    #                         key=lambda x: x[1], reverse=True)[:num_phrases]
    # top_n_tweets = sorted(popular_tweets, 
    #                         key=lambda x: x.popularity_score, 
    #                         reverse=True)[:num_tweets]
    
    # top_n_entities: List[EntityObj] = []

    # for (entity, url), count in top_n_entities_raw:
    #     top_n_entities.append(EntityObj(name=entity, url=url, count=count))

    # sentiment_avg_by_date = {}
    # for day, scores in sentiment_by_date.items():
    #     avg = sum(scores) / len(scores)
    #     sentiment_avg_by_date[day] = avg

    # logger.info("created all objects for dashboard data")
    # return DashboardData(
    #     language = language_counts,
    #     sentiment = sentiment_counts,
    #     sentiment_date = sentiment_avg_by_date,
    #     volume = volume_by_date, 
    #     entities = top_n_entities, 
    #     key_phrases = top_n_phrases, 
    #     popular_tweets = top_n_tweets
    # )




