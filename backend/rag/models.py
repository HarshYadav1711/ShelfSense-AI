from django.db import models


class RagQueryCache(models.Model):
    cache_key = models.CharField(max_length=128, unique=True)
    question = models.TextField()
    top_k = models.PositiveSmallIntegerField(default=4)
    index_stamp = models.CharField(max_length=64)
    response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class RagChatHistory(models.Model):
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list)
    related_books = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
