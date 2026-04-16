from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from django.db import transaction

from books.models import Book, BookInsight, IngestionStatus

from .llm import LocalLLMError

_LEGACY_SUMMARY_FP = re.compile(r"^\[fp:([a-f0-9]+)\] (.*)$", re.DOTALL)


INSIGHT_TYPES = ("summary", "genre", "recommendation", "sentiment")


def _local_llm_client():
    # Lazy-loaded to prevent blocking app startup
    from .llm import LocalLLMClient

    return LocalLLMClient()


def generate_insights_for_books(limit: int = 10) -> dict[str, int]:
    books = Book.objects.filter(ingestion_status=IngestionStatus.COMPLETED).order_by("-updated_at")[:limit]
    generated = 0
    skipped = 0

    llm = _local_llm_client()
    for book in books:
        if _is_insight_cache_fresh(book):
            skipped += 1
            continue

        insight_payload = _build_insight_payload(book=book, llm=llm)
        _store_insights(book=book, insight_payload=insight_payload)
        generated += 1

    return {"generated": generated, "skipped": skipped}


def _build_insight_payload(book: Book, llm: Any) -> dict[str, str]:
    prompt = (
        "Return valid JSON with keys summary, genre, recommendation, sentiment.\n"
        "Keep each value short, factual, and grounded in the provided book data.\n"
        f"Title: {book.title}\n"
        f"Author: {book.author or 'Unknown'}\n"
        f"Rating: {book.rating if book.rating is not None else 'Unknown'}\n"
        f"Description: {book.description or 'No description available.'}"
    )
    try:
        payload = llm.generate_json(prompt)
        return {
            "summary": str(payload.get("summary", "")).strip(),
            "genre": str(payload.get("genre", "")).strip(),
            "recommendation": str(payload.get("recommendation", "")).strip(),
            "sentiment": str(payload.get("sentiment", "")).strip(),
        }
    except (LocalLLMError, ValueError, TypeError, json.JSONDecodeError):
        return _fallback_insights(book)


def _fallback_insights(book: Book) -> dict[str, str]:
    description = book.description or "No description is available."
    return {
        "summary": description[:220].strip(),
        "genre": _guess_genre(description),
        "recommendation": _recommendation_from_rating(book.rating),
        "sentiment": _sentiment_from_rating(book.rating),
    }


def _guess_genre(description: str) -> str:
    lowered = description.lower()
    if "murder" in lowered or "detective" in lowered:
        return "Mystery"
    if "magic" in lowered or "dragon" in lowered:
        return "Fantasy"
    if "love" in lowered or "romance" in lowered:
        return "Romance"
    return "General Fiction"


def _recommendation_from_rating(rating) -> str:
    if rating is None:
        return "Recommend after reading a sample chapter."
    if float(rating) >= 4:
        return "Strongly recommended for most readers."
    if float(rating) >= 3:
        return "Recommended if the theme matches reader interest."
    return "Consider alternatives unless the topic is a strong fit."


def _sentiment_from_rating(rating) -> str:
    if rating is None:
        return "Neutral sentiment due to missing rating."
    if float(rating) >= 4:
        return "Positive"
    if float(rating) >= 3:
        return "Mixed"
    return "Negative"


def _book_fingerprint(book: Book) -> str:
    material = f"{book.title}|{book.author}|{book.rating}|{book.description}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _split_legacy_fingerprint_content(content: str) -> tuple[str | None, str]:
    """Parse legacy ``[fp:hex] ...`` summary prefix; return (fingerprint or None, body)."""
    m = _LEGACY_SUMMARY_FP.match(content or "")
    if not m:
        return None, content or ""
    return m.group(1), m.group(2)


def _summary_fingerprint_for_cache(insight: BookInsight) -> str | None:
    """Fingerprint used for cache invalidation: metadata first, else legacy content prefix."""
    md = insight.metadata or {}
    fp = md.get("fingerprint")
    if isinstance(fp, str) and len(fp) == 64:
        return fp
    legacy_fp, _ = _split_legacy_fingerprint_content(insight.content or "")
    return legacy_fp


def display_insight_content(insight: BookInsight) -> str:
    """User-facing insight text (strips legacy embedded fingerprint from summary if present)."""
    if insight.insight_type != "summary":
        return insight.content or ""
    legacy_fp, body = _split_legacy_fingerprint_content(insight.content or "")
    if legacy_fp is not None:
        return body
    return insight.content or ""


def _is_insight_cache_fresh(book: Book) -> bool:
    existing = {insight.insight_type: insight for insight in book.insights.all()}
    if not all(insight_type in existing for insight_type in ("summary", "genre", "recommendation")):
        return False
    expected = _book_fingerprint(book)
    current = _summary_fingerprint_for_cache(existing["summary"])
    return current == expected


@transaction.atomic
def _store_insights(book: Book, insight_payload: dict[str, Any]) -> None:
    fingerprint = _book_fingerprint(book)
    meta = {"fingerprint": fingerprint}
    for insight_type in INSIGHT_TYPES:
        content = str(insight_payload.get(insight_type) or "").strip()
        if not content:
            continue

        BookInsight.objects.update_or_create(
            book=book,
            insight_type=insight_type,
            defaults={
                "content": content,
                "ingestion_status": IngestionStatus.COMPLETED,
                "metadata": meta,
            },
        )
