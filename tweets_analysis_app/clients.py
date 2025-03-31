import os
from dotenv import load_dotenv
from azure.search.documents.aio import SearchClient
from azure.keyvault.secrets.aio import SecretClient
from openai import AsyncAzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
load_dotenv()

search_client: SearchClient | None = None

async def init_search_client() -> SearchClient:
    global search_client
    if search_client is not None:
        return search_client
    
    credential = DefaultAzureCredential()
    keyvault_uri = os.getenv("KEY_VAULT_URI")
    keyvault_client = SecretClient(vault_url=keyvault_uri, credential=credential)

    async with keyvault_client:
        search_endpoint = await (keyvault_client.get_secret("SEARCH-ENDPOINT")).value
        search_key = await (keyvault_client.get_secret("SEARCH-KEY")).value
        search_index = await (keyvault_client.get_secret("SEARCH-INDEX-NAME")).value

    return SearchClient(endpoint=search_endpoint, index_name=search_index,
                                    credential=AzureKeyCredential(search_key))