from rest_framework import serializers


class RagIndexRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(min_value=1, max_value=500, default=200)


class RagQuestionRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    top_k = serializers.IntegerField(min_value=1, max_value=8, default=4)
