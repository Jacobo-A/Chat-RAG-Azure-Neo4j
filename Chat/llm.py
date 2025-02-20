from langchain_openai import AzureChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.graph_transformers import LLMGraphTransformer
import torch
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv(".env", override=True)

def get_chat_llm():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

def get_embeddings():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HuggingFaceEmbeddings(
        model_name='sentence-transformers/all-mpnet-base-v2',
        model_kwargs={"device": device}  # Usa GPU si está disponible
    )

def get_doc_transformer():
    return LLMGraphTransformer(
        llm=get_chat_llm()
    )
