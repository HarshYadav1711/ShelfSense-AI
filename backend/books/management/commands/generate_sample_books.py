from django.core.management.base import BaseCommand

from books.models import Book, IngestionStatus
from ingestion.services import _replace_chunks
from insights.services import generate_insights_for_books
from rag.services import run_indexing


SAMPLE_BOOKS = [
    {
        "source_id": "sample-001",
        "title": "Practical Retrieval Systems",
        "author": "Ana Brooks",
        "rating": 4.4,
        "reviews_count": 120,
        "description": "A practical guide to building grounded retrieval systems with clear evaluation patterns.",
        "book_url": "https://example.local/books/sample-001",
    },
    {
        "source_id": "sample-002",
        "title": "Metadata at Scale",
        "author": "Leo Martin",
        "rating": 4.0,
        "reviews_count": 88,
        "description": "Covers robust metadata pipelines, repeatable ingestion jobs, and idempotent processing.",
        "book_url": "https://example.local/books/sample-002",
    },
    {
        "source_id": "sample-003",
        "title": "Applied Recommendation Patterns",
        "author": "Maya Chen",
        "rating": 3.8,
        "reviews_count": 67,
        "description": "Explains recommendation logic, user-facing confidence, and transparent source citations.",
        "book_url": "https://example.local/books/sample-003",
    },
]


class Command(BaseCommand):
    help = "Generate clean local sample books, then insights and vector index."

    def handle(self, *args, **options):
        for payload in SAMPLE_BOOKS:
            book, _created = Book.objects.update_or_create(
                source_site="sample.local",
                source_id=payload["source_id"],
                defaults={
                    **payload,
                    "ingestion_status": IngestionStatus.COMPLETED,
                },
            )
            _replace_chunks(book=book, text=book.description)

        insights = generate_insights_for_books(limit=len(SAMPLE_BOOKS))
        indexing = run_indexing(limit=30)
        self.stdout.write(
            self.style.SUCCESS(
                f"Sample data ready. insights_generated={insights['generated']} indexed={indexing['indexed']}"
            )
        )
