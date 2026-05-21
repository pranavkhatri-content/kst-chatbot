"""
retriever.py — Given a user query, embed it and find the top-k most
relevant KST knowledge chunks from ChromaDB.
"""

import os
import httpx
import chromadb

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-embedding-001:embedContent"
)
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# Lazy-load the client and collection
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_collection("kst_knowledge")
    return _collection


def embed_query(text: str) -> list[float]:
    resp = httpx.post(
        EMBED_URL,
        params={"key": GEMINI_API_KEY},
        json={"model": "models/gemini-embedding-001", "content": {"parts": [{"text": text}]}},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Embedding error {resp.status_code}: {resp.text}")
    return resp.json()["embedding"]["values"]


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Returns a list of the top_k most relevant chunks, each with:
      - content  (str)
      - topic    (str)
      - doc_url  (str)
      - score    (float, lower = more similar for cosine distance)
    """
    collection = _get_collection()
    query_emb = embed_query(query)

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "content": doc,
            "topic": meta["topic"],
            "doc_url": meta["doc_url"],
            "score": round(dist, 4),
        })

    return chunks


def build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context string for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}: {c['topic']}]\n"
            f"Documentation: {c['doc_url']}\n"
            f"{c['content']}"
        )
    return "\n\n---\n\n".join(parts)
