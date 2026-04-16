"""
End-to-end pipeline test: real DB, chunking, insights, and indexing.

Only ``ingestion.services.scrape_books`` is mocked (fake ``ScrapedBook`` rows).

Uses a temporary ``CHROMA_PERSIST_DIR`` and clears the embedding model cache so
runs are isolated. First run on a machine may download the sentence-transformers
model (subsequent runs use the HF cache and are faster). On Windows, Chroma keeps
files open; ``TemporaryDirectory(ignore_cleanup_errors=True)`` avoids teardown
errors.
"""

from __future__ import annotations

import os
import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from books.models import Book, BookChunk, BookInsight, IngestionStatus
from ingestion.models import PipelineJob
from ingestion.pipeline import launch_pipeline_job, run_pipeline_job_once
from scraper.books_to_scrape import ScrapedBook


def _long_description(seed: str) -> str:
    """Enough words for multiple overlapping chunks (max_words=80, overlap=20)."""
    return " ".join(f"{seed} word{i} repeat" for i in range(120))


def _clear_embedding_model_cache() -> None:
    from rag.services import _embedding_model

    if hasattr(_embedding_model, "_cache"):
        delattr(_embedding_model, "_cache")


class PipelineEndToEndTests(TestCase):
    """PipelineJob + run_pipeline_job_once with mocked scrape_books only."""

    @patch("ingestion.services.scrape_books")
    def test_pipeline_creates_books_chunks_insights_and_completes_job(self, mock_scrape):
        mock_scrape.return_value = [
            ScrapedBook(
                source_id="e2e-upc-a",
                title="E2E Book Alpha",
                author="Tester One",
                rating=Decimal("4.50"),
                reviews_count=12,
                description=_long_description("alpha"),
                book_url="https://books.toscrape.com/catalogue/e2e-alpha/index.html",
            ),
            ScrapedBook(
                source_id="e2e-upc-b",
                title="E2E Book Beta",
                author="Tester Two",
                rating=Decimal("3.25"),
                reviews_count=3,
                description=_long_description("beta"),
                book_url="https://books.toscrape.com/catalogue/e2e-beta/index.html",
            ),
        ]

        # Chroma keeps mmap/file handles open; on Windows temp cleanup can fail unless ignored.
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as chroma_dir:
            env = {**os.environ, "CHROMA_PERSIST_DIR": chroma_dir}
            with patch.dict(os.environ, env, clear=False):
                _clear_embedding_model_cache()

                job = launch_pipeline_job(limit=10, max_pages=1)
                self.assertIsInstance(job, PipelineJob)
                self.assertEqual(job.status, IngestionStatus.PENDING)

                run_pipeline_job_once(job.id)

                job.refresh_from_db()
                self.assertEqual(job.status, IngestionStatus.COMPLETED)
                self.assertEqual(job.stage, "completed")
                self.assertEqual(job.progress_percent, 100)
                self.assertEqual(job.error_message, "")
                self.assertIn("ingestion", job.details or {})
                self.assertIn("insights", job.details or {})
                self.assertIn("indexing", job.details or {})
                idx = (job.details or {}).get("indexing") or {}
                self.assertGreater(idx.get("indexed", 0), 0)

                books = list(Book.objects.order_by("title"))
                self.assertEqual(len(books), 2)
                self.assertEqual({b.title for b in books}, {"E2E Book Alpha", "E2E Book Beta"})
                self.assertTrue(all(b.ingestion_status == IngestionStatus.COMPLETED for b in books))

                total_chunks = BookChunk.objects.count()
                self.assertGreater(total_chunks, 0)
                for book in books:
                    self.assertGreater(book.chunks.count(), 0, msg=f"expected chunks for {book.title}")

                insight_rows = BookInsight.objects.filter(book__in=books)
                self.assertGreaterEqual(
                    insight_rows.count(),
                    6,
                    msg="expect at least summary, genre, recommendation for each book",
                )
                for book in books:
                    types = set(book.insights.values_list("insight_type", flat=True))
                    self.assertTrue({"summary", "genre", "recommendation"}.issubset(types))
