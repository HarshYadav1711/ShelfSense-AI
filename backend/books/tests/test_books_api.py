"""Integration tests for book list and detail APIs."""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book, BookInsight, IngestionStatus


class BooksAPIIntegrationTests(TestCase):
    """GET /api/v1/books/ and GET /api/v1/books/<id>/."""

    def setUp(self):
        self.client = APIClient()

    def test_list_empty_database(self):
        response = self.client.get("/api/v1/books/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn("count", body)
        self.assertIn("results", body)
        self.assertEqual(body["count"], 0)
        self.assertEqual(body["results"], [])

    def test_list_pagination_and_search(self):
        Book.objects.create(
            source_site="test",
            source_id="a",
            title="Alpha Unique",
            author="Author A",
            rating=Decimal("4.00"),
            description="metadata pipeline story",
            book_url="https://example.com/a",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        Book.objects.create(
            source_site="test",
            source_id="b",
            title="Beta Other",
            author="Author B",
            rating=Decimal("3.00"),
            description="unrelated",
            book_url="https://example.com/b",
            ingestion_status=IngestionStatus.COMPLETED,
        )

        r1 = self.client.get("/api/v1/books/", {"page": 1, "page_size": 1})
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        data = r1.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

        r2 = self.client.get("/api/v1/books/", {"search": "Alpha"})
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        data2 = r2.json()
        self.assertEqual(data2["count"], 1)
        self.assertEqual(data2["results"][0]["title"], "Alpha Unique")

    def test_detail_returns_insights_and_metadata(self):
        book = Book.objects.create(
            source_site="test",
            source_id="d1",
            title="Detail Book",
            author="Writer",
            rating=Decimal("4.50"),
            reviews_count=10,
            description="Full description text here.",
            book_url="https://example.com/d1",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=book,
            insight_type="summary",
            content="Short summary.",
            ingestion_status=IngestionStatus.COMPLETED,
        )

        response = self.client.get(f"/api/v1/books/{book.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], book.id)
        self.assertEqual(body["title"], "Detail Book")
        self.assertEqual(body["author"], "Writer")
        self.assertEqual(float(body["rating"]), 4.5)
        self.assertEqual(body["reviews_count"], 10)
        self.assertEqual(body["description"], "Full description text here.")
        self.assertEqual(body["book_url"], "https://example.com/d1")
        self.assertEqual(body["ingestion_status"], IngestionStatus.COMPLETED)
        self.assertEqual(len(body["insights"]), 1)
        self.assertEqual(body["insights"][0]["insight_type"], "summary")

    def test_detail_not_found(self):
        response = self.client.get("/api/v1/books/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("message", response.json())

    def test_list_invalid_min_rating_returns_400(self):
        response = self.client.get("/api/v1/books/", {"min_rating": "not-a-number"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.json())

    @patch("books.views.related_book_ids_via_embeddings")
    def test_related_books_uses_embedding_ranking_when_available(self, mock_embed_ids):
        base = Book.objects.create(
            source_site="test",
            source_id="r0",
            title="Source Book",
            author="A",
            rating=Decimal("4.00"),
            description="Shared theme alpha bravo",
            book_url="https://example.com/r0",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        second = Book.objects.create(
            source_site="test",
            source_id="r1",
            title="Second",
            author="B",
            rating=Decimal("5.00"),
            description="Other",
            book_url="https://example.com/r1",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        third = Book.objects.create(
            source_site="test",
            source_id="r2",
            title="Third",
            author="C",
            rating=Decimal("3.00"),
            description="Other",
            book_url="https://example.com/r2",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        mock_embed_ids.return_value = [third.id, second.id]

        response = self.client.get(f"/api/v1/books/{base.id}/related/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["book_id"], base.id)
        self.assertEqual([row["id"] for row in body["results"]], [third.id, second.id])

    @patch("books.views.related_book_ids_via_embeddings")
    def test_related_books_falls_back_to_genre_when_embeddings_unavailable(self, mock_embed_ids):
        mock_embed_ids.return_value = None
        main = Book.objects.create(
            source_site="test",
            source_id="m1",
            title="Main",
            author="A",
            rating=Decimal("4.00"),
            description="Desc",
            book_url="https://example.com/m1",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        match = Book.objects.create(
            source_site="test",
            source_id="m2",
            title="Match",
            author="B",
            rating=Decimal("5.00"),
            description="D",
            book_url="https://example.com/m2",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        no_overlap = Book.objects.create(
            source_site="test",
            source_id="m3",
            title="NoGenreOverlap",
            author="C",
            rating=Decimal("5.00"),
            description="D",
            book_url="https://example.com/m3",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=main,
            insight_type="genre",
            content="Science Fiction",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=match,
            insight_type="genre",
            content="Science Fiction anthology",
            ingestion_status=IngestionStatus.COMPLETED,
        )
        BookInsight.objects.create(
            book=no_overlap,
            insight_type="genre",
            content="Cooking",
            ingestion_status=IngestionStatus.COMPLETED,
        )

        response = self.client.get(f"/api/v1/books/{main.id}/related/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["book_id"], main.id)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["id"], match.id)
