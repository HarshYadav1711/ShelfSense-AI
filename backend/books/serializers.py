from rest_framework import serializers

from .models import Book, BookInsight


class BookInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookInsight
        fields = ["insight_type", "content", "updated_at"]


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "description",
            "book_url",
            "updated_at",
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    insights = BookInsightSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "rating",
            "reviews_count",
            "description",
            "book_url",
            "ingestion_status",
            "last_ingested_at",
            "insights",
            "created_at",
            "updated_at",
        ]


class UploadProcessRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10)
    max_pages = serializers.IntegerField(min_value=1, max_value=20, default=3)
