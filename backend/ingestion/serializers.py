from rest_framework import serializers

from .models import IngestionRun, PipelineJob


class IngestionRunRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10)
    max_pages = serializers.IntegerField(min_value=1, max_value=20, default=3)


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


class PipelineJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineJob
        fields = [
            "id",
            "status",
            "stage",
            "progress_percent",
            "limit",
            "max_pages",
            "ingestion_run_id",
            "details",
            "error_message",
            "last_heartbeat_at",
            "created_at",
            "updated_at",
        ]
