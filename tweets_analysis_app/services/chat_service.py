import re, json
from typing import AsyncGenerator, List
from aiocache import cached
from azure.search.documents.models import VectorizableTextQuery
from tweets_analysis_app.models.chat import ChatRequest, Message
from tweets_analysis_app.clients import get_azure_clients
import logging

logger = logging.getLogger(__name__)


rewrite_system_prompt = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge.
    You have access to Azure AI Search index with 100's of documents.
    Generate a search query based on the conversation and the new question.
    Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
    Do not include any text inside [] or <<>> in the search query terms.
    Do not include any special characters like '+'.
    If the question is not in English, translate the question to English before generating the search query.
    If you cannot generate a search query, return just the number 0.
    """

rewrite_few_shots = [
    {
        "role": "user",
        "content": "What are people saying about vaccines?"
    },
    {
        "role": "assistant",
        "content": "vaccine shots kids immunity booster"
    },
    {
        "role": "user",
        "content": "Is there any concern about flu season?"
    },
    {
        "role": "assistant",
        "content": "flu cases cough symptoms getting sick"
    },
    {
        "role": "user",
        "content": "What are the public's thoughts on masks?"
    },
    {
        "role": "assistant",
        "content": "mask mandate wearing face covering safety rules"
    },
    {
        "role": "user",
        "content": "Are people confused about travel rules?"
    },
    {
        "role": "assistant",
        "content": "travel restrictions airport covid rules testing"
    },
    {
        "role": "user",
        "content": "Any talk about new viruses?"
    },
    {
        "role": "assistant",
        "content": "new virus symptoms outbreak warning"
    }
]


rag_system_prompt1 = """
You are an intelligent assistant designed to help CDC leaders and the general public understand what people are discussing in relation to the CDC, based on real tweet text.

You are given a list of tweets that contain the term “CDC” or “Centers for Disease Control” and were retrieved because they are relevant to the user's question. Your job is to analyze these tweets and generate a clear, helpful, and accurate answer.

Use only the text of the tweets to inform your response. Do not rely on external knowledge, assumptions, or inferred sentiment. If the tweets do not contain enough information to answer the question, clearly say so.

Summarize the key **themes, opinions, facts, or repeated ideas** that appear across multiple tweets. Do not simply list points from each tweet. Instead, synthesize them into a brief, cohesive summary that helps the user understand what the public is saying. Do not mention that the content came from tweets unless the user asks. Just state the content directly.

Avoid speculation about the tweet authors, demographics, or intent. Do not include usernames, timestamps, or links. Do not refer to sentiment, engagement, or trends, unless they are explicitly mentioned in the tweet text.

At the end of your response, suggest **3 very brief follow-up questions** the user might logically ask next to better understand the topic. These questions must be answerable using tweet text alone and should invite further exploration of what the public is saying. Return only the questions enclosed in double angle brackets, without any introductory phrases or text.
DO NOT SAY 'Here are some follow-up questions you might consider' or any other introductory preamble. Example:
<<Are people raising concerns about vaccine data?>>
<<What are the most frequently mentioned health topics?>>
<<Are any public health policies being discussed?>>
Do not repeat previously asked questions.
Make sure the final follow-up ends with ">>".
"""
rag_system_prompt = """
You are an intelligent assistant designed to help CDC leaders and the general public understand what people are discussing in relation to the CDC, based on real tweet text.

You are given a list of tweets that contain the term “CDC” or “Centers for Disease Control” and were retrieved because they may be relevant to the user's question. Your job is to analyze only these tweets and generate a clear, helpful, and accurate answer.

You MUST use only the content of these tweets to inform your response. You are not allowed to make assumptions, inferences, or guesses based on world knowledge or associations. Do NOT include information unless it is directly and unambiguously supported by the tweet text.

If the tweets do not contain enough information to answer the user's question — or if the specific topic mentioned by the user is NOT present in the tweets — you MUST say so clearly and briefly.

Your goal is to identify key themes, repeated opinions, or commonly mentioned facts across the tweets, but ONLY if these points are clearly stated in the tweet text. Do NOT speculate about intentions or imply causality unless explicitly written in the tweet.

NEVER say or imply that the tweets mention something that they actually do not. If the list of tweets are NOT sufficient to accurately and specifically answer the user's question, say exactly that and NEVER generalize from partial matches.

When unsure if the tweets are sufficient, ALWAYS say there is not enough information rather than partially answering the user's question.

Do not mention that your answer is based on tweets. Do not include usernames, links, or tweet metadata. Just state the content as plain informative statements.

At the end of your response, generate 3 very short follow-up questions that the user might ask next to better explore what people are discussing. IMPORTANT: End your answer with exactly three follow-up questions enclosed in << >>. NEVER FORGET THIS.
Enclose them in double angle brackets, and do NOT include any preamble or labels before them. For example, after you answer a user's question, you would add only this:
<<What concerns are being raised about vaccine safety?>>
<<Are people questioning the CDC's communication strategies?>>
<<What specific public health issues are frequently mentioned?>>
Do not repeat previously asked questions.
Make sure the last follow-up ends with ">>".
"""


def extract_followups(content: str) -> List[str]:

    questions = re.findall(r"<<(.*?)>>", content)
    return questions

async def rewrite_query(messages: List[Message]) -> str:
    clients = get_azure_clients()
    openai_client = clients.openai_client

    user_query = messages[-1].content
    rewrite_messages = [{"role": "system", "content": rewrite_system_prompt}] + rewrite_few_shots
    rewrite_messages.append({"role": "user", "content": f"Generate search query for: {user_query}"})


    try:
        completion = await openai_client.chat.completions.create(
            model=clients.openai_completions_deployment,
            messages=rewrite_messages,
            temperature=0.0,
            max_tokens=100,
        )
        logging.info(f"OpenAI response: {completion}")
        response = completion.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("Error in rewrite_query: %s", e)
        raise

    if not response or response == "0":
        return user_query
    return response

async def stream_chat_response(request: ChatRequest) -> AsyncGenerator[str, None]:
    clients = get_azure_clients()
    search_client = clients.search_client
    openai_client = clients.openai_client

    user_query = request.messages[-1].content
    logging.info(f"User query: {user_query}")
    try:
        rewritten_query = await rewrite_query(request.messages)
        logging.info(f"Rewritten query: {rewritten_query}")

        results = await search_client.search(
            vector_queries=[VectorizableTextQuery(
                text=rewritten_query, 
                k_nearest_neighbors=10,
                fields="text_vector"
            )], 
            filter="language eq 'en'",
            select=["text", "created_at", "source_url"]
        )

        docs = [doc async for doc in results]
        context = "\n".join([f"- {doc.get('text')}" for doc in docs])
        logging.info(context)

        rag_messages = [{"role": "system", "content": rag_system_prompt}]

        rag_messages += [msg.model_dump() for msg in request.messages[:-1]]

        rag_messages.append({
            "role": "user",
            "content": f"{user_query}\n\nContext:\n{context}"
        })

        yield {
            "choices": [{
                "delta": {"role": "assistant"},
                "index": 0,
            }],
            "object": "chat.completion.chunk"
        }

        followup_started = False
        followup_content = ""
        stream = await openai_client.chat.completions.create(
            model=clients.openai_completions_deployment,
            messages=rag_messages,
            temperature=0.7, 
            stream=True
        )

        async for event_chunk in stream:
            chunk = event_chunk.model_dump()
            if not chunk.get("choices") or not chunk["choices"]:
                continue 
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content") or ""
            logging.info(f"Content: {content}")
            if "<<" in content:
                followup_started = True
                before = content[:content.index("<<")].strip()
                after = content[content.index("<<"):].strip()
                if before:
                    chunk["choices"][0]["delta"]["content"] = before
                    yield chunk
                followup_content += after
            elif followup_started:
                followup_content += content
            else:
                yield chunk
            
        citations = [
            {
                "url": doc.get("source_url"), 
                "snippet": re.sub(r'\s+', ' ', doc.get("text", "")).strip(), 
                "date": doc.get("created_at")
            }
            for doc in docs if doc.get("source_url")
        ]

        followup_questions = []
        if followup_content:
            logging.info(followup_content)
            followup_questions = extract_followups(followup_content)
            logging.info(followup_questions)
            
        yield {
            "choices": [{
                "delta": {"role": "assistant"},
                "context": {
                    "data_points": citations,
                    "followup_questions": followup_questions
                },
                "index": 0,
                "finish_reason": "stop"
            }],
            "object": "chat.completion.chunk"
        }
    except Exception as e:
        logging.exception("Error in stream_chat_response: %s", e)
        raise


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    try:
        async for event in r:
            yield json.dumps(event) + "\n"
    except Exception as error:
        logging.exception("Exception while generating response stream: %s", error)
        yield json.dumps({"error": str(error)}) + "\n"


@cached(ttl=60)
async def get_search_suggestions(query: str) -> List[str]:
    clients = get_azure_clients()
    search_client = clients.search_client

    if not query.strip():
        return []
    
    results = await search_client.suggest(
        search_text=query, 
        suggester_name=clients.search_suggester, 
        use_fuzzy_matching=True,
        top=5
    )

    suggestions = [result["text"] for result in results]
    logging.info(suggestions)
    return suggestions