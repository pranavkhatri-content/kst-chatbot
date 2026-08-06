"""
retriever.py — Given a user query, embed it locally and find the top-k most
relevant KST knowledge chunks from ChromaDB.

Embeddings run fully locally via sentence-transformers — no API calls, no cost.
"""

import os
import chromadb

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# Lazy-load the client, collection and embedding model
_client = None
_collection = None
_embedder = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_collection("kst_knowledge")
    return _collection


def _get_embedder():
    global _embedder
    if _embedder is None:
        # Imported here so the model only loads when first needed
        # (first ever run downloads ~80MB from HuggingFace, then cached locally)
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def embed_query(text: str) -> list[float]:
    return _get_embedder().encode(text, normalize_embeddings=True).tolist()


def retrieve(query: str, top_k: int = 3, max_distance: float = 1.0) -> list[dict]:
    """
    Returns up to top_k relevant chunks whose cosine distance is below
    max_distance.  Each result dict contains:
      - content   (str)
      - chunk_id  (str)
      - topic     (str)
      - doc_url   (str)
      - score     (float, lower = more similar for cosine distance)

    Each chunk is indexed as MULTIPLE vectors (topic + every anticipated
    query phrasing — see ingest.py). This over-fetches raw vector matches,
    then collapses to the single best-scoring vector per chunk_id before
    applying top_k, so a chunk isn't penalised just because only one of its
    several phrasings matched.
    """
    collection = _get_collection()
    query_emb = embed_query(query)

    n_results = min(collection.count(), max(top_k * 12, 30))
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    best_per_chunk: dict[str, tuple] = {}
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        cid = meta["chunk_id"]
        if cid not in best_per_chunk or dist < best_per_chunk[cid][2]:
            best_per_chunk[cid] = (doc, meta, dist)

    ranked = sorted(best_per_chunk.values(), key=lambda x: x[2])

    chunks = []
    for doc, meta, dist in ranked:
        if len(chunks) >= top_k:
            break
        if dist > max_distance:
            print(f"  [{round(dist, 4)}] SKIP {meta['topic']} (over threshold)")
            break
        print(f"  [{round(dist, 4)}] {meta['topic']}")
        chunks.append({
            "content": doc,
            "chunk_id": meta.get("chunk_id"),
            "topic": meta["topic"],
            "doc_url": meta["doc_url"],
            "score": round(dist, 4),
        })

    if not chunks:
        print(f"  ! All results exceeded max_distance={max_distance}")

    return chunks


def retrieve_conversational(latest_query: str, context_query: str,
                            top_k: int = 3, max_distance: float = 1.0) -> list[dict]:
    """
    Dual-query retrieval for multi-turn conversations.

    A single joined query ("What is KST? How do I set up Shopify?") lets the
    earlier topic dominate the embedding and drown out the current question.
    Instead, run both queries and merge:
      - primary:  the latest user message alone -> top 2 (current question wins)
      - context:  the joined conversation query -> top 2 unseen
                  (rescues ambiguous follow-ups like "what about the conversion tag?")
    Returns up to top_k + 1 unique chunks (4 with the default top_k=3).
    """
    print(f"  [primary query] {ascii(latest_query)}")
    primary = retrieve(latest_query, top_k=top_k, max_distance=max_distance)
    merged = primary[:2]
    seen = {c["chunk_id"] for c in merged}
    cap = top_k + 1

    if context_query and context_query.strip() != latest_query.strip():
        print(f"  [context query] {ascii(context_query)}")
        for c in retrieve(context_query, top_k=top_k, max_distance=max_distance):
            if len(merged) >= cap:
                break
            if c["chunk_id"] not in seen:
                merged.append(c)
                seen.add(c["chunk_id"])
    else:
        # Single-turn conversation: primary is the only signal
        merged = primary

    return merged


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
