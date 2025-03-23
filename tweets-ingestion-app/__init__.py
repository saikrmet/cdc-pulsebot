import os
import json
import logging
import datetime
import azure.functions as func

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import tweepy


def main(dailytimer: func.TimerRequest) -> None:
    """Function that pulls tweets about the Centers for Disease Control 
    and Prevention (CDC), format for AI Search index, and push to blob storage.

    Parameters:
        - dailytimer: trigger that defines how often to run function app

    Returns:
        - None
    """
    logging.info("Started CDC Tweet Ingestion Function App")

    credential = DefaultAzureCredential()

    keyvault_uri = os.environ["KEY_VAULT_URL"]
    keyvault_client = SecretClient(vault_url=keyvault_uri, credential=credential)

    twitter_token = keyvault_client.get_secret("TWITTER-BEARER-TOKEN")

    client = tweepy.Client(bearer_token=twitter_token)