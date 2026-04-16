from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from books.models import BookChunk, IngestionStatus
from insights.llm import LocalLLMClient, LocalLLMError


EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "shelfsense-book-chunks")


def run_indexing(limit: int = 200) -> dict[str, int]:
    model = _embedding_model()
    collection = _collection()
    chunks = (
        BookChunk.objects.select_related("book")
        .filter(book__ingestion_status=IngestionStatus.COMPLETED)
        .order_by("-updated_at")[:limit]
    )

    indexed = 0
    skipped = 0
    for chunk in chunks:
        chunk_hash = _chunk_hash(chunk.content)
        doc_id = _chunk_id(chunk)
        existing = collection.get(ids=[doc_id], include=["metadatas"])
        if existing.get("ids") and existing["ids"][0]:
            metadata = existing["metadatas"][0]
            if metadata and metadata.get("content_hash") == chunk_hash:
                skipped += 1
                continue

        embedding = model.encode(chunk.content).tolist()
        metadata = {
            "book_id": chunk.book_id,
            "book_title": chunk.book.title,
            "chunk_index": chunk.chunk_index,
            "book_url": chunk.book.book_url,
            "content_hash": chunk_hash,
        }
        collection.upsert(
            ids=[doc_id],
            documents=[chunk.content],
            embeddings=[embedding],
            metadatas=[metadata],
        )
        indexed += 1

    return {"indexed": indexed, "skipped": skipped}


def answer_question(question: str, top_k: int = 4) -> dict[str, Any]:
    model = _embedding_model()
    collection = _collection()
    llm = LocalLLMClient()

    query_embedding = model.encode(question).tolist()
    result = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    context_items = _build_context_items(result)
    context_text = _context_block(context_items)

    prompt = (
        "Answer only from the context. If context is insufficient, say you do not know.\n"
        "Keep answer concise and factual.\n\n"
        f"Question: {question}\n\nContext:\n{context_text}"
    )

    try:
        answer = llm.generate_text(prompt)
    except LocalLLMError:
        answer = "I do not know based on the indexed book context."

    return {
        "answer": answer.strip(),
        "sources": [
            {
                "book_id": item["book_id"],
                "book_title": item["book_title"],
                "book_url": item["book_url"],
                "chunk_index": item["chunk_index"],
                "similarity_distance": item["distance"],
            }
            for item in context_items
        ],
        "related_books": sorted({item["book_title"] for item in context_items}),
        "metadata": {
            "top_k": top_k,
            "retrieved_chunks": len(context_items),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "collection": CHROMA_COLLECTION_NAME,
        },
    }


def _build_context_items(query_result: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    documents = query_result.get("documents", [[]])[0]
    metadatas = query_result.get("metadatas", [[]])[0]
    distances = query_result.get("distances", [[]])[0]

    for document, metadata, distance in zip(documents, metadatas, distances):
        if metadata is None:
            continue
        items.append(
            {
                "content": document,
                "book_id": metadata.get("book_id"),
                "book_title": metadata.get("book_title"),
                "book_url": metadata.get("book_url"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": round(float(distance), 4) if distance is not None else None,
            }
        )
    return items


def _context_block(context_items: list[dict[str, Any]]) -> str:
    if not context_items:
        return "No context found."
    return "\n\n".join(
        [
            (
                f"[Source {index + 1}] book={item['book_title']} chunk={item['chunk_index']}\n"
                f"{item['content']}"
            )
            for index, item in enumerate(context_items)
        ]
    )


def _embedding_model() -> SentenceTransformer:
    if not hasattr(_embedding_model, "_cache"):
        setattr(_embedding_model, "_cache", SentenceTransformer(EMBEDDING_MODEL_NAME))
    return getattr(_embedding_model, "_cache")


def _collection():
    persist_path = Path(os.getenv("CHROMA_PERSIST_DIR", "backend/.chroma")).resolve()
    client = chromadb.PersistentClient(path=str(persist_path))
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _chunk_id(chunk: BookChunk) -> str:
    return f"book-{chunk.book_id}-chunk-{chunk.chunk_index}"


def _chunk_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
