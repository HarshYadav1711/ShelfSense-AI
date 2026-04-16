import logging
import os
import threading
import time

from django.core.management.base import BaseCommand
from django.db import OperationalError, transaction
from django.utils import timezone

from books.models import IngestionStatus

from ingestion.models import PipelineJob
from ingestion.pipeline import run_pipeline_job_once
from ingestion.worker_recovery import reset_stale_processing_jobs

logger = logging.getLogger(__name__)

_DEFAULT_STALE_THRESHOLD_SEC = int(os.getenv("PIPELINE_STALE_HEARTBEAT_SECONDS", "300"))
_DEFAULT_HEARTBEAT_INTERVAL_SEC = float(os.getenv("PIPELINE_HEARTBEAT_INTERVAL_SECONDS", "15"))


class Command(BaseCommand):
    help = "Polls PipelineJob rows and executes the ingestion pipeline one job at a time."

    def add_arguments(self, parser):
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds to sleep when no pending jobs are available.",
        )
        parser.add_argument(
            "--stale-threshold-seconds",
            type=int,
            default=_DEFAULT_STALE_THRESHOLD_SEC,
            help=(
                "On startup: mark processing jobs with heartbeat older than this as failed "
                f"(default: env PIPELINE_STALE_HEARTBEAT_SECONDS or {_DEFAULT_STALE_THRESHOLD_SEC})."
            ),
        )
        parser.add_argument(
            "--heartbeat-interval",
            type=float,
            default=_DEFAULT_HEARTBEAT_INTERVAL_SEC,
            help=(
                "While a job runs, refresh last_heartbeat_at at this interval in seconds "
                f"(default: env PIPELINE_HEARTBEAT_INTERVAL_SECONDS or {_DEFAULT_HEARTBEAT_INTERVAL_SEC})."
            ),
        )

    def handle(self, *args, **options):
        poll_interval: float = options["poll_interval"]
        stale_threshold: int = max(1, int(options["stale_threshold_seconds"]))
        heartbeat_interval: float = max(1.0, float(options["heartbeat_interval"]))

        n = reset_stale_processing_jobs(stale_threshold)
        if n:
            self.stdout.write(
                self.style.WARNING(f"Recovered {n} stale processing job(s) (threshold {stale_threshold}s).")
            )

        self.stdout.write(self.style.NOTICE("Pipeline worker started. Press Ctrl+C to stop."))

        try:
            while True:
                job = self._claim_next_job()
                if job is None:
                    time.sleep(poll_interval)
                    continue

                logger.info("pipeline.worker.claimed job_id=%s status=%s stage=%s", job.id, job.status, job.stage)
                stop = threading.Event()

                def heartbeat_loop() -> None:
                    while not stop.wait(timeout=heartbeat_interval):
                        try:
                            rows = PipelineJob.objects.filter(
                                id=job.id,
                                status=IngestionStatus.PROCESSING,
                            ).update(last_heartbeat_at=timezone.now(), updated_at=timezone.now())
                            if rows == 0:
                                return
                        except Exception:
                            logger.exception("pipeline.worker.heartbeat_failed job_id=%s", job.id)

                hb = threading.Thread(target=heartbeat_loop, name=f"pipeline-hb-{job.id}", daemon=True)
                hb.start()
                try:
                    run_pipeline_job_once(job.id)
                except Exception:
                    logger.exception("pipeline.worker.unhandled job_id=%s", job.id)
                finally:
                    stop.set()
                    hb.join(timeout=heartbeat_interval + 2.0)
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
                job.last_heartbeat_at = timezone.now()
                job.save(
                    update_fields=[
                        "status",
                        "stage",
                        "progress_percent",
                        "error_message",
                        "updated_at",
                        "last_heartbeat_at",
                    ]
                )
                logger.info(
                    "pipeline.worker.claim job_id=%s previous_status=%s",
                    job.id,
                    previous_status,
                )
                return job
        except OperationalError as exc:
            logger.warning("pipeline.worker.claim_failed error=%s", exc)
            return None
