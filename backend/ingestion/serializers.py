from rest_framework import serializers

from .models import IngestionRun


class IngestionRunRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10)


class IngestionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionRun
        fields = [
            "id",
            "source",
            "status",
            "requested_count",
            "processed_count",
            "failed_count",
            "error_message",
            "started_at",
            "finished_at",
        ]
