from __future__ import annotations

import logging

from books.models import IngestionStatus
from insights.services import generate_insights_for_books
from rag.services import run_indexing

from .models import PipelineJob
from .services import run_book_ingestion

logger = logging.getLogger(__name__)


def launch_pipeline_job(limit: int, max_pages: int) -> PipelineJob:
    job = PipelineJob.objects.create(
        status=IngestionStatus.PENDING,
        stage="queued",
        progress_percent=0,
        limit=limit,
        max_pages=max_pages,
    )
    logger.info(
        "pipeline.launch enqueued job_id=%s limit=%s max_pages=%s",
        job.id,
        limit,
        max_pages,
    )
    return job


def run_pipeline_job_once(job_id: int) -> None:
    """
    Execute the full pipeline for a single job.

    Intended to be called by the DB-backed worker after the job row is claimed
    (status=processing). Row locking happens in the worker claim transaction; this
    function performs the long-running work without holding that DB transaction open.
    """
    job = PipelineJob.objects.get(id=job_id)

    logger.info("pipeline.start job_id=%s stage=%s status=%s", job.id, job.stage, job.status)

    try:
        _update_job(job, stage="ingestion", percent=5)
        logger.info("pipeline.stage job_id=%s stage=ingestion", job.id)

        ingestion_run = run_book_ingestion(limit=job.limit, max_pages=job.max_pages, job=job)
        logger.info(
            "pipeline.ingestion_done job_id=%s run_id=%s run_status=%s processed=%s failed=%s",
            job.id,
            ingestion_run.id,
            ingestion_run.status,
            ingestion_run.processed_count,
            ingestion_run.failed_count,
        )

        _update_job(job, stage="insights", percent=75)
        logger.info("pipeline.stage job_id=%s stage=insights", job.id)
        insight_stats = generate_insights_for_books(limit=job.limit)
        logger.info("pipeline.insights_done job_id=%s stats=%s", job.id, insight_stats)

        _update_job(job, stage="indexing", percent=90)
        logger.info("pipeline.stage job_id=%s stage=indexing", job.id)
        index_stats = run_indexing(limit=job.limit * 4)
        logger.info("pipeline.indexing_done job_id=%s stats=%s", job.id, index_stats)

        job.details = {
            "ingestion": {
                "run_id": ingestion_run.id,
                "status": ingestion_run.status,
                "processed_count": ingestion_run.processed_count,
                "failed_count": ingestion_run.failed_count,
            },
            "insights": insight_stats,
            "indexing": index_stats,
        }
        _update_job(job, stage="completed", percent=100, status=IngestionStatus.COMPLETED)
        logger.info("pipeline.complete job_id=%s", job.id)
    except Exception as exc:
        job.error_message = str(exc)
        _update_job(job, stage="failed", percent=100, status=IngestionStatus.FAILED)
        logger.exception("pipeline.failed job_id=%s error=%s", job.id, exc)


# Backwards-compatible name for internal references / docs.
_run_pipeline_job = run_pipeline_job_once


def _update_job(job: PipelineJob, stage: str, percent: int, status: str = IngestionStatus.PROCESSING) -> None:
    job.status = status
    job.stage = stage
    job.progress_percent = percent
    job.save(update_fields=["status", "stage", "progress_percent", "details", "error_message", "updated_at"])
