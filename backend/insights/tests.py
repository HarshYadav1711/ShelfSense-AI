"""Tests for insight fingerprint cache and user-facing content."""

from decimal import Decimal

from django.test import TestCase

from books.models import Book, BookInsight, IngestionStatus

from insights.services import (
    _book_fingerprint,
    _is_insight_cache_fresh,
    display_insight_content,
)


class InsightFingerprintTests(TestCase):
    def _make_book(self) -> Book:
        return Book.objects.create(
            source_site="test",
            source_id="fp1",
            title="T",
            author="A",
            rating=Decimal("4.00"),
            description="Desc",
            book_url="https://example.com/fp1",
            ingestion_status=IngestionStatus.COMPLETED,
        )

    def test_cache_fresh_uses_metadata_fingerprint(self):
        book = self._make_book()
        fp = _book_fingerprint(book)
        BookInsight.objects.create(
            book=book,
            insight_type="summary",
            content="Clean summary text.",
            metadata={"fingerprint": fp},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="genre",
            content="Fiction",
            metadata={"fingerprint": fp},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="recommendation",
            content="Read it",
            metadata={"fingerprint": fp},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        self.assertTrue(_is_insight_cache_fresh(book))

    def test_cache_fresh_legacy_prefixed_summary(self):
        book = self._make_book()
        fp = _book_fingerprint(book)
        BookInsight.objects.create(
            book=book,
            insight_type="summary",
            content=f"[fp:{fp}] Legacy summary.",
            metadata={},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="genre",
            content="Fiction",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="recommendation",
            content="Read it",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        self.assertTrue(_is_insight_cache_fresh(book))

    def test_cache_stale_when_fingerprint_mismatch(self):
        book = self._make_book()
        BookInsight.objects.create(
            book=book,
            insight_type="summary",
            content="Summary",
            metadata={"fingerprint": "0" * 64},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="genre",
            content="Fiction",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="recommendation",
            content="Read it",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        self.assertFalse(_is_insight_cache_fresh(book))

    def test_display_strips_legacy_prefix(self):
        book = self._make_book()
        fp = _book_fingerprint(book)
        insight = BookInsight(
            book=book,
            insight_type="summary",
            content=f"[fp:{fp}] Only the good part.",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        self.assertEqual(display_insight_content(insight), "Only the good part.")

    def test_display_clean_summary_unchanged(self):
        book = self._make_book()
        insight = BookInsight(
            book=book,
            insight_type="summary",
            content="Already clean.",
            metadata={"fingerprint": _book_fingerprint(book)},
            ingestion_status=IngestionStatus.COMPLETED,
        )
        self.assertEqual(display_insight_content(insight), "Already clean.")
