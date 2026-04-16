from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any
from django.utils import timezone

import chromadb
from sentence_transformers import SentenceTransformer

from books.models import BookChunk, IngestionStatus
from insights.llm import LocalLLMClient, LocalLLMError
from .models import RagChatHistory, RagQueryCache


EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "shelfsense-book-chunks")


def _embedding_to_list(raw: Any) -> list:
    """Normalize SentenceTransformer output (tensor) or test doubles (plain list)."""
    if hasattr(raw, "tolist"):
        return raw.tolist()
    if isinstance(raw, (list, tuple)):
        return list(raw)
    return list(raw)


def _encode_many(model: SentenceTransformer, contents: list[str]) -> list[list[float]]:
    """Batch-encode chunk texts; returns one embedding vector per input row."""
    if not contents:
        return []
    raw = model.encode(contents)
    if isinstance(raw, list):
        return [_embedding_to_list(row) for row in raw]
    shape = getattr(raw, "shape", None)
    if shape is not None and len(shape) == 2:
        return [_embedding_to_list(raw[i]) for i in range(int(shape[0]))]
    if shape is not None and len(shape) == 1:
        return [_embedding_to_list(raw)]
    return [_embedding_to_list(model.encode(text)) for text in contents]


def run_indexing(limit: int = 200, batch_size: int = 100) -> dict[str, int]:
    """
    Index up to ``limit`` book chunks into Chroma, newest-first.

    Chunks are loaded and embedded in batches of ``batch_size`` to limit memory
    use on large corpora. Skips unchanged rows using ``content_hash`` (same as
    single-chunk upserts).
    """
    if batch_size < 1:
        batch_size = 100

    model = _embedding_model()
    collection = _collection()
    base_qs = (
        BookChunk.objects.select_related("book")
        .filter(book__ingestion_status=IngestionStatus.COMPLETED)
        .order_by("-updated_at")
    )

    indexed = 0
    skipped = 0
    offset = 0

    while offset < limit:
        take = min(batch_size, limit - offset)
        chunks = list(base_qs[offset : offset + take])
        if not chunks:
            break

        doc_ids = [_chunk_id(c) for c in chunks]
        existing = collection.get(ids=doc_ids, include=["metadatas"])
        existing_ids = existing.get("ids") or []
        metadatas = existing.get("metadatas") or []
        id_to_meta: dict[str, Any] = {}
        for i, eid in enumerate(existing_ids):
            id_to_meta[eid] = metadatas[i] if i < len(metadatas) else None

        pending: list[tuple[BookChunk, str, str]] = []
        for chunk in chunks:
            chunk_hash = _chunk_hash(chunk.content)
            doc_id = _chunk_id(chunk)
            metadata = id_to_meta.get(doc_id)
            if metadata is not None and metadata.get("content_hash") == chunk_hash:
                skipped += 1
                continue
            pending.append((chunk, chunk_hash, doc_id))

        if pending:
            contents = [c.content for c, _, _ in pending]
            embeddings = _encode_many(model, contents)
            ids = [doc_id for _, _, doc_id in pending]
            metadatas_out = [
                {
                    "book_id": c.book_id,
                    "book_title": c.book.title,
                    "chunk_index": c.chunk_index,
                    "book_url": c.book.book_url,
                    "content_hash": h,
                }
                for c, h, _ in pending
            ]
            collection.upsert(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas_out,
            )
            indexed += len(pending)

        offset += len(chunks)
        if len(chunks) < take:
            break

    return {"indexed": indexed, "skipped": skipped}


def answer_question(question: str, top_k: int = 4) -> dict[str, Any]:
    cache_key = _cache_key(question=question, top_k=top_k)
    cached = RagQueryCache.objects.filter(cache_key=cache_key).first()
    if cached:
        payload = cached.response
        _save_chat_history(payload=payload, question=question)
        payload["metadata"]["cache_hit"] = True
        return payload

    model = _embedding_model()
    collection = _collection()
    llm = LocalLLMClient()

    query_embedding = _embedding_to_list(model.encode(question))
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

    payload = {
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
            "cache_hit": False,
        },
    }
    RagQueryCache.objects.update_or_create(
        cache_key=cache_key,
        defaults={
            "question": question,
            "top_k": top_k,
            "index_stamp": _index_stamp(),
            "response": payload,
        },
    )
    _save_chat_history(payload=payload, question=question)
    return payload


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


def _index_stamp() -> str:
    latest_chunk = BookChunk.objects.order_by("-updated_at").values_list("updated_at", flat=True).first()
    if latest_chunk is None:
        return "empty"
    return timezone.localtime(latest_chunk).isoformat()


def _cache_key(question: str, top_k: int) -> str:
    raw = f"{question.strip().lower()}|{top_k}|{_index_stamp()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _save_chat_history(payload: dict[str, Any], question: str) -> None:
    RagChatHistory.objects.create(
        question=question,
        answer=payload.get("answer", ""),
        sources=payload.get("sources", []),
        related_books=payload.get("related_books", []),
    )
