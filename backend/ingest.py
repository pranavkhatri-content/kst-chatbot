"""
ingest.py — Run this once (or whenever knowledge_chunks.py changes) to
embed all KST knowledge chunks and store them in ChromaDB.

Embeddings run fully locally via sentence-transformers — no API key needed.

Usage:
    python ingest.py
"""

import os
import chromadb
from dotenv import load_dotenv
from knowledge_chunks import CHUNKS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Reuse the exact same embedder as retrieval so vectors always match
from retriever import embed_query as get_embedding

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")


def main():
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete and recreate collection so re-runs are idempotent
    try:
        client.delete_collection("kst_knowledge")
        print("Deleted existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="kst_knowledge",
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Embedding {len(CHUNKS)} chunks locally (multi-vector)...")
    ids, embeddings, documents, metadatas = [], [], [], []

    for i, chunk in enumerate(CHUNKS):
        # Embed the topic and EACH anticipated query phrasing as its OWN
        # vector — never blended into one string.
        #
        # Concatenating them into a single sequence before pooling measurably
        # hurts retrieval: mean-pooling averages every token in the blob, so
        # a chunk's own most-relevant phrasing gets diluted by its siblings.
        # Verified empirically — the bare phrase "what is KST" alone scores
        # 0.98 cosine similarity against the query "What is KST?"; blended
        # into the full topic+queries text for that chunk, similarity drops
        # to ~0.5, well below unrelated chunks. Also excludes `content`
        # entirely — it runs 400-550 tokens, the embedder truncates at 256,
        # and long/generic chunks were winning retrieval purely on length.
        #
        # Every vector for a chunk shares its chunk_id/doc/metadata so they
        # can all point at the same document. Retrieval (retriever.py)
        # over-fetches raw vector matches, then collapses to the single
        # best-scoring vector per chunk_id before applying top_k.
        texts = [chunk["topic"]] + chunk.get("queries", [])
        print(f"  [{i+1}/{len(CHUNKS)}] {chunk['id']} ({len(texts)} vectors)")
        for j, text in enumerate(texts):
            emb = get_embedding(text)
            ids.append(f"{chunk['id']}::{j}")
            embeddings.append(emb)
            documents.append(chunk["content"])
            metadatas.append({
                "chunk_id": chunk["id"],
                "topic": chunk["topic"],
                "doc_url": chunk["doc_url"],
            })

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"\nDone! {len(CHUNKS)} chunks -> {len(ids)} query vectors stored in "
          f"ChromaDB at: {CHROMA_PATH}")
    print("You can now start the API server with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
