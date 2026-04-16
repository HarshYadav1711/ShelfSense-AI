"""
Stale pipeline job detection for single-worker DB polling workers.

Jobs left in ``processing`` without a recent heartbeat are treated as abandoned
(e.g. crashed worker, OOM kill) and marked ``failed`` so they can be retried
explicitly or superseded by new jobs — never double-executed.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from books.models import IngestionStatus

from .models import PipelineJob

logger = logging.getLogger(__name__)


def reset_stale_processing_jobs(threshold_seconds: int) -> int:
    """
    Mark ``processing`` jobs as ``failed`` when heartbeat is older than the threshold.

    Uses ``last_heartbeat_at`` when set; otherwise falls back to ``updated_at`` for
    rows predating the heartbeat field (null heartbeat + old update time).

    Returns the number of rows updated.
    """
    if threshold_seconds < 1:
        threshold_seconds = 60

    cutoff = timezone.now() - timedelta(seconds=threshold_seconds)
    stale_message = (
        f"Stale job: no worker heartbeat within {threshold_seconds}s "
        "(process likely crashed or was terminated)."
    )

    qs = PipelineJob.objects.filter(status=IngestionStatus.PROCESSING).filter(
        Q(last_heartbeat_at__lt=cutoff)
        | Q(last_heartbeat_at__isnull=True, updated_at__lt=cutoff)
    )
    updated = qs.update(
        status=IngestionStatus.FAILED,
        stage="failed",
        progress_percent=100,
        error_message=stale_message,
        updated_at=timezone.now(),
    )
    if updated:
        logger.warning(
            "pipeline.worker.recovery marked %s stale processing job(s) (threshold=%ss)",
            updated,
            threshold_seconds,
        )
    return updated
