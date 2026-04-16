from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import Path
import sys
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from books.models import Book, BookChunk, IngestionStatus

from .models import IngestionLog, IngestionRun, PipelineJob


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scraper.books_to_scrape import ScrapedBook, scrape_books  # noqa: E402


def run_book_ingestion(limit: int = 10, max_pages: int = 3, job: PipelineJob | None = None) -> IngestionRun:
    run = IngestionRun.objects.create(
        status=IngestionStatus.PROCESSING,
        requested_count=limit,
    )
    if job is not None:
        job.ingestion_run = run
        _set_job_progress(job, stage="scraping", percent=10)

    try:
        scraped_books = scrape_books(limit=limit, max_pages=max_pages)
        processed_count = 0
        failed_count = 0

        for scraped_book in scraped_books:
            normalized_book = _normalize_scraped_book(scraped_book)
            try:
                _persist_scraped_book(run=run, scraped_book=normalized_book)
                processed_count += 1
            except Exception as exc:
                failed_count += 1
                IngestionLog.objects.create(
                    run=run,
                    status=IngestionStatus.FAILED,
                    message=f"Failed '{normalized_book.title}': {exc}",
                )
            if job is not None and scraped_books:
                progress = 10 + int((processed_count + failed_count) / len(scraped_books) * 60)
                _set_job_progress(job, stage="ingesting", percent=min(progress, 70))

        run.status = IngestionStatus.COMPLETED
        run.processed_count = processed_count
        run.failed_count = failed_count
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "processed_count", "failed_count", "finished_at"])
    except Exception as exc:
        run.status = IngestionStatus.FAILED
        run.error_message = str(exc)
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "error_message", "finished_at"])
        IngestionLog.objects.create(
            run=run,
            status=IngestionStatus.FAILED,
            message=f"Ingestion failed: {exc}",
        )
        if job is not None:
            _set_job_progress(job, stage="failed", percent=100, error_message=str(exc))

    return run


def _normalize_scraped_book(scraped_book: ScrapedBook) -> ScrapedBook:
    payload = asdict(scraped_book)
    payload["title"] = " ".join(payload["title"].split())
    payload["author"] = _normalize_optional_text(payload["author"])
    payload["description"] = _normalize_optional_text(payload["description"])
    payload["book_url"] = payload["book_url"].strip()
    return ScrapedBook(**payload)


def _normalize_optional_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


@transaction.atomic
def _persist_scraped_book(run: IngestionRun, scraped_book: ScrapedBook) -> None:
    book, _created = Book.objects.update_or_create(
        source_site="books.toscrape.com",
        source_id=scraped_book.source_id,
        defaults={
            "title": scraped_book.title,
            "author": scraped_book.author or "",
            "rating": scraped_book.rating,
            "reviews_count": scraped_book.reviews_count,
            "description": scraped_book.description or "",
            "book_url": scraped_book.book_url,
            "ingestion_status": IngestionStatus.PROCESSING,
            "last_ingested_at": timezone.now(),
        },
    )

    _replace_chunks(book=book, text=book.description)

    book.ingestion_status = IngestionStatus.COMPLETED
    book.save(update_fields=["ingestion_status", "updated_at"])

    IngestionLog.objects.create(
        run=run,
        book=book,
        status=IngestionStatus.COMPLETED,
        message=f"Ingested '{book.title}'",
    )


def _replace_chunks(book: Book, text: str) -> None:
    chunks = _chunk_text(text)
    book.chunks.all().delete()

    if not chunks:
        return

    BookChunk.objects.bulk_create(
        [
            BookChunk(
                book=book,
                chunk_index=index,
                content=chunk,
                metadata={
                    "source": "description",
                    "word_count": len(chunk.split()),
                    "content_hash": _content_hash(chunk),
                },
            )
            for index, chunk in enumerate(chunks)
        ]
    )


def _chunk_text(text: str, max_words: int = 80, overlap_words: int = 20) -> Iterable[str]:
    words = text.split()
    if not words:
        return []
    if overlap_words >= max_words:
        overlap_words = max_words // 2

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap_words
    return chunks


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _set_job_progress(
    job: PipelineJob,
    stage: str,
    percent: int,
    error_message: str = "",
) -> None:
    job.stage = stage
    job.progress_percent = max(0, min(100, percent))
    if error_message:
        job.error_message = error_message
        job.status = IngestionStatus.FAILED
    elif stage == "completed":
        job.status = IngestionStatus.COMPLETED
    else:
        job.status = IngestionStatus.PROCESSING
    job.last_heartbeat_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "stage",
            "progress_percent",
            "error_message",
            "updated_at",
            "ingestion_run",
            "last_heartbeat_at",
        ]
    )
