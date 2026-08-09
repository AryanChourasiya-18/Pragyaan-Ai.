"""Thin wrapper around ChromaDB for per-document RAG collections."""
from typing import List

import chromadb
from chromadb.utils import embedding_functions

from app.config import settings

_client = chromadb.PersistentClient(path=settings.chroma_dir)

_embedder = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.openai_api_key,
    model_name=settings.embedding_model,
)


def collection_name_for(document_id: str) -> str:
    return f"doc_{document_id.replace('-', '')}"


def index_chunks(document_id: str, chunks: List[dict]) -> str:
    name = collection_name_for(document_id)
    collection = _client.get_or_create_collection(name=name, embedding_function=_embedder)

    ids = [f"{document_id}-{i}" for i in range(len(chunks))]
    texts = [c["text"] for c in chunks]
    metadatas = [{"page": c["page"]} for c in chunks]

    if texts:
        collection.add(ids=ids, documents=texts, metadatas=metadatas)

    return name


def query_similar(document_id: str, query: str, top_k: int = 5):
    name = collection_name_for(document_id)
    collection = _client.get_or_create_collection(name=name, embedding_function=_embedder)
    results = collection.query(query_texts=[query], n_results=top_k)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        hits.append({"text": doc, "page": meta.get("page")})
    return hits
