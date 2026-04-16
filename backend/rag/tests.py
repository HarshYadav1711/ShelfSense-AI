from unittest.mock import patch

from django.test import TestCase

from rag.services import _build_context_items, answer_question


class RagFormattingTests(TestCase):
    def test_build_context_items_maps_metadata(self):
        query_result = {
            "documents": [["alpha text"]],
            "metadatas": [[{"book_id": 4, "book_title": "Alpha", "book_url": "http://example.com/a", "chunk_index": 2}]],
            "distances": [[0.12345]],
        }
        items = _build_context_items(query_result)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["book_title"], "Alpha")
        self.assertEqual(items[0]["chunk_index"], 2)
        self.assertEqual(items[0]["distance"], 0.1235)

    @patch("rag.services.LocalLLMClient")
    @patch("rag.services._embedding_model")
    @patch("rag.services._collection")
    def test_answer_question_returns_expected_shape(self, mock_collection, mock_embedding_model, mock_llm):
        mock_embedding_model.return_value.encode.return_value = [0.1, 0.2, 0.3]
        mock_collection.return_value.query.return_value = {
            "documents": [["book chunk text"]],
            "metadatas": [
                [
                    {
                        "book_id": 1,
                        "book_title": "Book One",
                        "book_url": "http://example.com/book-1",
                        "chunk_index": 0,
                    }
                ]
            ],
            "distances": [[0.2]],
        }
        mock_llm.return_value.generate_text.return_value = "Grounded answer."

        payload = answer_question(question="What is this book about?", top_k=3)

        self.assertIn("answer", payload)
        self.assertIn("sources", payload)
        self.assertIn("related_books", payload)
        self.assertIn("metadata", payload)
        self.assertEqual(payload["answer"], "Grounded answer.")
        self.assertEqual(payload["related_books"], ["Book One"])
        self.assertEqual(payload["metadata"]["top_k"], 3)
