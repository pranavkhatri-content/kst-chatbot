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

    print(f"Embedding {len(CHUNKS)} chunks locally...")
    ids, embeddings, documents, metadatas = [], [], [], []

    for i, chunk in enumerate(CHUNKS):
        queries_block = "\n".join(chunk.get("queries", []))
        text = f"{chunk['topic']}\n\n{queries_block}\n\n{chunk['content']}"
        print(f"  [{i+1}/{len(CHUNKS)}] {chunk['id']}")
        emb = get_embedding(text)
        ids.append(chunk["id"])
        embeddings.append(emb)
        documents.append(chunk["content"])
        metadatas.append({
            "topic": chunk["topic"],
            "doc_url": chunk["doc_url"],
        })

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"\nDone! {len(CHUNKS)} chunks stored in ChromaDB at: {CHROMA_PATH}")
    print("You can now start the API server with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
