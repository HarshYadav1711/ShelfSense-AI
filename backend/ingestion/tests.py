from datetime import timedelta

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from books.models import IngestionStatus

from ingestion.models import PipelineJob
from ingestion.services import _chunk_text
from ingestion.worker_recovery import reset_stale_processing_jobs


class ChunkingTests(SimpleTestCase):
    def test_chunk_text_uses_overlap(self):
        text = " ".join([f"w{i}" for i in range(0, 30)])
        chunks = _chunk_text(text, max_words=10, overlap_words=2)
        self.assertEqual(len(chunks), 4)
        # Overlap check: last 2 words of chunk 1 appear first in chunk 2.
        first_words = chunks[0].split()
        second_words = chunks[1].split()
        self.assertEqual(first_words[-2:], second_words[:2])


class WorkerRecoveryTests(TestCase):
    def test_marks_stale_processing_job_failed(self):
        old = timezone.now() - timedelta(minutes=30)
        job = PipelineJob.objects.create(
            status=IngestionStatus.PROCESSING,
            stage="ingestion",
            progress_percent=50,
            limit=5,
            max_pages=1,
            last_heartbeat_at=old,
        )
        n = reset_stale_processing_jobs(threshold_seconds=60)
        self.assertEqual(n, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, IngestionStatus.FAILED)
        self.assertEqual(job.stage, "failed")
        self.assertIn("Stale job", job.error_message)

    def test_skips_recent_heartbeat(self):
        PipelineJob.objects.create(
            status=IngestionStatus.PROCESSING,
            stage="ingestion",
            progress_percent=50,
            limit=5,
            max_pages=1,
            last_heartbeat_at=timezone.now(),
        )
        n = reset_stale_processing_jobs(threshold_seconds=300)
        self.assertEqual(n, 0)

    def test_null_heartbeat_uses_updated_at(self):
        old = timezone.now() - timedelta(minutes=30)
        job = PipelineJob.objects.create(
            status=IngestionStatus.PROCESSING,
            stage="ingestion",
            progress_percent=50,
            limit=5,
            max_pages=1,
            last_heartbeat_at=None,
        )
        PipelineJob.objects.filter(pk=job.pk).update(updated_at=old)
        n = reset_stale_processing_jobs(threshold_seconds=60)
        self.assertEqual(n, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, IngestionStatus.FAILED)
