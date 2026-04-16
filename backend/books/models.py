from django.db import models


class IngestionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Book(models.Model):
    source_site = models.CharField(max_length=64, default="books.toscrape.com")
    source_id = models.CharField(max_length=128)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    reviews_count = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    book_url = models.URLField(unique=True)
    ingestion_status = models.CharField(
        max_length=16,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    last_ingested_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_site", "source_id"],
                name="unique_book_per_source",
            )
        ]

    def __str__(self):
        return self.title


class BookChunk(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["book_id", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["book", "chunk_index"],
                name="unique_chunk_per_book",
            )
        ]

    def __str__(self):
        return f"{self.book.title} [{self.chunk_index}]"


class BookInsight(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="insights")
    insight_type = models.CharField(max_length=64)
    content = models.TextField()
    ingestion_status = models.CharField(
        max_length=16,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["book_id", "insight_type", "-created_at"]

    def __str__(self):
        return f"{self.book.title} - {self.insight_type}"
