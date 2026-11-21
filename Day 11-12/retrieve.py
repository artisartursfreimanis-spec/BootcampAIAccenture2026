"""Retrieval: embed the query, search ChromaDB, return the chunks with metadata.

    uv run python retrieve.py "How many PTO days do employees get?"
"""

import sys
import time

import chromadb
from openai import OpenAI

import config


def get_collection() -> chromadb.Collection:
    chroma_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    return chroma_client.get_collection(name=config.COLLECTION_NAME)


def retrieve_chunks(query: str, top_k: int = config.TOP_K) -> dict:
    """Returns the top_k chunks in rank order with source, page and cosine similarity."""
    start = time.time()

    client = OpenAI(base_url=config.EMBEDDING_BASE_URL, api_key=config.EMBEDDING_API_KEY)
    query_embedding = client.embeddings.create(model=config.EMBEDDING_MODEL, input=[query]).data[0].embedding

    results = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    elapsed_ms = round((time.time() - start) * 1000)

    retrieved_chunks = [
        {
            "content": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "page": results["metadatas"][0][i]["page"],
            "relevance_score": round(1 - results["distances"][0][i], 4),
        }
        for i in range(len(results["ids"][0]))
    ]

    return {
        "query": query,
        "retrieved_chunks": retrieved_chunks,
        "retrieval_time_ms": elapsed_ms,
        "top_k": top_k,
        "embedding_model": config.EMBEDDING_MODEL,
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the remote work policy?"
    result = retrieve_chunks(q)
    print(f"Query: {result['query']}")
    print(f"Retrieved {len(result['retrieved_chunks'])} chunks in {result['retrieval_time_ms']} ms\n")
    for i, chunk in enumerate(result["retrieved_chunks"], start=1):
        print(f"--- {i}. score {chunk['relevance_score']} | {chunk['source']} p.{chunk['page']} ---")
        print(chunk["content"][:300])
        print()
