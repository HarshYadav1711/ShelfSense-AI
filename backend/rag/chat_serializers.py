from rest_framework import serializers

from .models import RagChatHistory


class RagChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RagChatHistory
        fields = ["id", "question", "answer", "sources", "related_books", "created_at"]
