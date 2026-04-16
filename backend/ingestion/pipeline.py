from __future__ import annotations

from threading import Thread

from books.models import IngestionStatus
from insights.services import generate_insights_for_books
from rag.services import run_indexing

from .models import PipelineJob
from .services import run_book_ingestion


def launch_pipeline_job(limit: int, max_pages: int) -> PipelineJob:
    job = PipelineJob.objects.create(
        status=IngestionStatus.PENDING,
        stage="queued",
        progress_percent=0,
        limit=limit,
        max_pages=max_pages,
    )
    worker = Thread(target=_run_pipeline_job, args=(job.id,), daemon=True)
    worker.start()
    return job


def _run_pipeline_job(job_id: int) -> None:
    job = PipelineJob.objects.get(id=job_id)
    try:
        _update_job(job, stage="ingestion", percent=5)
        ingestion_run = run_book_ingestion(limit=job.limit, max_pages=job.max_pages, job=job)

        _update_job(job, stage="insights", percent=75)
        insight_stats = generate_insights_for_books(limit=job.limit)

        _update_job(job, stage="indexing", percent=90)
        index_stats = run_indexing(limit=job.limit * 4)

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
    except Exception as exc:
        job.error_message = str(exc)
        _update_job(job, stage="failed", percent=100, status=IngestionStatus.FAILED)


def _update_job(job: PipelineJob, stage: str, percent: int, status: str = IngestionStatus.PROCESSING) -> None:
    job.status = status
    job.stage = stage
    job.progress_percent = percent
    job.save(update_fields=["status", "stage", "progress_percent", "details", "error_message", "updated_at"])
