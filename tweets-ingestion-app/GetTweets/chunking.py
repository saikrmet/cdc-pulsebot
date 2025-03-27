from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tiktoken
import hashlib

def chunk_text(text: str, chunk_size: int, chunk_overlap: int, 
                     encoding_model: str) -> list[str]:
    """Function to produce list of chunks from input text.

    Parameters:
        - text: input text from tweet (None checks in main)
        - chunk_size: number of tokens per chunk
        - chunk_overlap: number of token overlap between chunks
        - encoding_model: name of model used to compute number of tokens

    Returns:
        - list[str]: array of chunks corresponding to the input text
    """

    splitter = RecursiveCharacterTextSplitter(
        # Optimize chunk size and overlap
        separators=["\n\n", "\n", ".", " ", ""], 
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap, 
        length_function=lambda t: count_tokens(t, encoding_model)
        )

    chunk_list = []
    documents = splitter.create_documents([text])
    for doc in documents:
        chunk_list.append(doc.page_content)
    return chunk_list

def count_tokens(text: str, encoding_model: str) -> int:
    """Function to count the expected number of tokens necessary to embed the
    input text. 

    Paramaters:
        - text: input string
        - encoding_model: the name of the encoding model to compute tokens
    
    Returns:
        - int: number of expected tokens to embed text
    """

    tokenizer = tiktoken.encoding_for_model(encoding_model)
    return len(tokenizer.encode(text=text))

def generate_chunk_id(id: int, text: str) -> str:
    """Function to generate unique chunk id that encodes changes and
    information about the input text.

    Paramaters:
        - id: parent id of input text record
        - text: input text string

    Returns:
        - str: unique id using hash to compute 10 digit encoding of text
    """

    return "{}-{}".format(hashlib.sha256(text.encode()).hexdigest()[:10])