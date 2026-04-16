"""Integration tests for book ingestion with mocked Selenium scraper."""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from books.models import Book, IngestionStatus
from ingestion.models import IngestionRun
from ingestion.services import run_book_ingestion
from scraper.books_to_scrape import ScrapedBook


class IngestionFlowIntegrationTests(TestCase):
    """run_book_ingestion with scrape_books mocked — no real browser or network."""

    @patch("ingestion.services.scrape_books")
    def test_ingestion_persists_books_idempotently(self, mock_scrape):
        mock_scrape.return_value = [
            ScrapedBook(
                source_id="upc-111",
                title="Mock Book One",
                author=None,
                rating=Decimal("4.00"),
                reviews_count=None,
                description="First test description for chunking.",
                book_url="https://books.toscrape.com/catalogue/mock-one/index.html",
            ),
            ScrapedBook(
                source_id="upc-222",
                title="Mock Book Two",
                author=None,
                rating=Decimal("3.00"),
                reviews_count=None,
                description="Second test description.",
                book_url="https://books.toscrape.com/catalogue/mock-two/index.html",
            ),
        ]

        run1 = run_book_ingestion(limit=10, max_pages=1)
        self.assertEqual(run1.status, IngestionStatus.COMPLETED)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(IngestionRun.objects.count(), 1)

        titles = set(Book.objects.values_list("title", flat=True))
        self.assertEqual(titles, {"Mock Book One", "Mock Book Two"})

        # Second run with same source_id updates in place (no duplicate rows)
        run2 = run_book_ingestion(limit=10, max_pages=1)
        self.assertEqual(run2.status, IngestionStatus.COMPLETED)
        self.assertEqual(Book.objects.count(), 2)
        self.assertEqual(IngestionRun.objects.count(), 2)
