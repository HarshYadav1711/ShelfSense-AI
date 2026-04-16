"""Integration tests for POST /api/v1/rag/ask/ with mocked ML stack."""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from rag.models import RagChatHistory, RagQueryCache


class RagAskAPIIntegrationTests(TestCase):
    """Validate RAG ask response shape and validation errors."""

    def setUp(self):
        self.client = APIClient()
        RagQueryCache.objects.all().delete()
        RagChatHistory.objects.all().delete()

    def _mock_stack(self, mock_llm_cls, mock_collection, mock_embed):
        embed = MagicMock()
        embed.encode.return_value = [0.1, 0.2, 0.3]
        mock_embed.return_value = embed

        collection = MagicMock()
        collection.query.return_value = {
            "documents": [["chunk text about books"]],
            "metadatas": [
                [
                    {
                        "book_id": 1,
                        "book_title": "Test Book",
                        "book_url": "https://example.com/b1",
                        "chunk_index": 0,
                    }
                ]
            ],
            "distances": [[0.15]],
        }
        mock_collection.return_value = collection

        llm = MagicMock()
        llm.generate_text.return_value = "Grounded answer from context."
        mock_llm_cls.return_value = llm

    @patch("rag.services.LocalLLMClient")
    @patch("rag.services._collection")
    @patch("rag.services._embedding_model")
    def test_ask_returns_expected_json_shape(self, mock_embed, mock_collection, mock_llm_cls):
        self._mock_stack(mock_llm_cls, mock_collection, mock_embed)

        response = self.client.post(
            "/api/v1/rag/ask/",
            {"question": "What is this book about?", "top_k": 4},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn("answer", body)
        self.assertIn("sources", body)
        self.assertIn("related_books", body)
        self.assertIn("metadata", body)
        self.assertEqual(body["answer"], "Grounded answer from context.")
        self.assertEqual(len(body["sources"]), 1)
        self.assertEqual(body["sources"][0]["book_title"], "Test Book")
        self.assertEqual(body["sources"][0]["chunk_index"], 0)
        self.assertIn("similarity_distance", body["sources"][0])
        self.assertEqual(body["metadata"]["top_k"], 4)
        self.assertEqual(body["metadata"]["cache_hit"], False)

    def test_ask_missing_question_returns_400(self):
        response = self.client.post("/api/v1/rag/ask/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ask_top_k_out_of_range_returns_400(self):
        response = self.client.post(
            "/api/v1/rag/ask/",
            {"question": "ok", "top_k": 99},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("rag.services.LocalLLMClient")
    @patch("rag.services._collection")
    @patch("rag.services._embedding_model")
    def test_ask_cache_hit_second_request(self, mock_embed, mock_collection, mock_llm_cls):
        self._mock_stack(mock_llm_cls, mock_collection, mock_embed)

        payload = {"question": "Same question twice", "top_k": 2}
        r1 = self.client.post("/api/v1/rag/ask/", payload, format="json")
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        r2 = self.client.post("/api/v1/rag/ask/", payload, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.json()["metadata"]["cache_hit"], True)
        # LLM should only be needed for first call if cache works
        self.assertEqual(mock_llm_cls.return_value.generate_text.call_count, 1)
