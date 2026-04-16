from rest_framework import serializers


class InsightGenerationRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=100, default=10)
