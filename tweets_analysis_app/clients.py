import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.keyvault.secrets.aio import SecretClient
from openai import AsyncAzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

_azure_clients_instance = None

class AzureClients:
    def __init__(self):
        self._credential = DefaultAzureCredential()
        self._token_provider = get_bearer_token_provider(self._credential, os.getenv("TOKEN_SCOPE"))
        self._keyvault_uri = os.getenv("KEY_VAULT_URI")
        self._secret_client = SecretClient(vault_url=self._keyvault_uri, 
                                          credential=self._credential)
        self.search_client = None
        self.openai_client = None
        self.openai_deployment = None

    async def init_clients(self):
        async with self._secret_client:
            search_endpoint = (await self._secret_client.get_secret("SEARCH-ENDPOINT")).value
            search_key = (await self._secret_client.get_secret("SEARCH-KEY")).value
            search_index_name = (await self._secret_client.get_secret("SEARCH-INDEX-NAME")).value
            openai_endpoint = (await self._secret_client.get_secret("OPENAI-ENDPOINT")).value
            openai_api_version = (await self._secret_client.get_secret("OPENAI-API-VERSION")).value
            self.openai_deployment = (await self._secret_client.get_secret("OPENAI-DEPLOYMENT-NAME"))

            self.search_client = SearchClient(endpoint=search_endpoint, index_name=search_index_name,
                                        credential=AzureKeyCredential(search_key))

            self.openai_client = AsyncAzureOpenAI(azure_endpoint=openai_endpoint, 
                                                azure_ad_token=self._token_provider,
                                                api_version=openai_api_version)
        
    def get_search_client(self):
        if self.search_client is None:
            raise Exception("Search client has not been initialized.")
        return self.search_client
    
    def get_openai_client(self):
        if self.openai_client is None:
            raise Exception("OpenAI client has not been initialized.")
        return self.openai_client

    
    async def close(self):
        await self.search_client.close()
        await self.openai_client.close()
        await self._credential.close()


def set_azure_clients(instance: AzureClients):
        global _azure_clients_instance
        _azure_clients_instance = instance

def get_azure_clients() -> AzureClients:
    if _azure_clients_instance is None:
        raise Exception("Azure clients instance has not been initialized")
    return _azure_clients_instance