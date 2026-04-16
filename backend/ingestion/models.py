from django.db import models

from books.models import Book, IngestionStatus


class IngestionRun(models.Model):
    source = models.CharField(max_length=128, default="books.toscrape.com")
    status = models.CharField(
        max_length=16,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    requested_count = models.PositiveIntegerField(default=0)
    processed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.source} - {self.started_at:%Y-%m-%d %H:%M:%S}"


class IngestionLog(models.Model):
    run = models.ForeignKey(IngestionRun, on_delete=models.CASCADE, related_name="logs")
    book = models.ForeignKey(
        Book,
        on_delete=models.SET_NULL,
        related_name="ingestion_logs",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=16, choices=IngestionStatus.choices)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.message


class PipelineJob(models.Model):
    status = models.CharField(
        max_length=16,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    stage = models.CharField(max_length=64, default="queued")
    progress_percent = models.PositiveSmallIntegerField(default=0)
    limit = models.PositiveIntegerField(default=10)
    max_pages = models.PositiveIntegerField(default=3)
    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pipeline_jobs",
    )
    details = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PipelineJob<{self.id}> {self.stage}"
