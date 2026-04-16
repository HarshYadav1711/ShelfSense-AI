from django.test import SimpleTestCase

from ingestion.services import _chunk_text


class ChunkingTests(SimpleTestCase):
    def test_chunk_text_uses_overlap(self):
        text = " ".join([f"w{i}" for i in range(0, 30)])
        chunks = _chunk_text(text, max_words=10, overlap_words=2)
        self.assertEqual(len(chunks), 4)
        # Overlap check: last 2 words of chunk 1 appear first in chunk 2.
        first_words = chunks[0].split()
        second_words = chunks[1].split()
        self.assertEqual(first_words[-2:], second_words[:2])
