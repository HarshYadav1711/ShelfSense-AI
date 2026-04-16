import logging
import time

from django.core.management.base import BaseCommand
from django.db import OperationalError, transaction

from books.models import IngestionStatus

from ingestion.models import PipelineJob
from ingestion.pipeline import run_pipeline_job_once

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Polls PipelineJob rows and executes the ingestion pipeline one job at a time."

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds to sleep when no pending jobs are available.",
        )

    def handle(self, *args, **options):
        poll_interval: float = options["poll_interval"]
        self.stdout.write(self.style.NOTICE("Pipeline worker started. Press Ctrl+C to stop."))

        try:
            while True:
                job = self._claim_next_job()
                if job is None:
                    time.sleep(poll_interval)
                    continue

                logger.info("pipeline.worker.claimed job_id=%s status=%s stage=%s", job.id, job.status, job.stage)
                try:
                    run_pipeline_job_once(job.id)
                except Exception:
                    logger.exception("pipeline.worker.unhandled job_id=%s", job.id)
        except KeyboardInterrupt:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Pipeline worker stopped (Ctrl+C)."))

    def _claim_next_job(self) -> PipelineJob | None:
        """
        Lock one eligible job and mark it processing.

        Uses select_for_update(skip_locked=True) on MySQL/Postgres. SQLite ignores
        row locks but still serializes writers; claim remains safe for a single worker.
        """
        try:
            with transaction.atomic():
                job = (
                    PipelineJob.objects.select_for_update(skip_locked=True)
                    .filter(status__in=[IngestionStatus.PENDING, IngestionStatus.FAILED])
                    .order_by("created_at")
                    .first()
                )
                if job is None:
                    return None

                previous_status = job.status
                job.status = IngestionStatus.PROCESSING
                job.stage = "claimed"
                job.progress_percent = 1
                job.error_message = ""
                job.save(update_fields=["status", "stage", "progress_percent", "error_message", "updated_at"])
                logger.info(
                    "pipeline.worker.claim job_id=%s previous_status=%s",
                    job.id,
                    previous_status,
                )
                return job
        except OperationalError as exc:
            logger.warning("pipeline.worker.claim_failed error=%s", exc)
            return None
