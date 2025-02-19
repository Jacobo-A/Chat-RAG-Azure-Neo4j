from langchain_experimental.graph_transformers import LLMGraphTransformer
from llm import get_chat_llm, get_embeddings
from neo4jDb import get_graph_db


llm_provider = get_chat_llm()
embedding_provider = get_embeddings()
graph = get_graph_db(database="rag")

doc_transformer = LLMGraphTransformer(llm=llm_provider)
