from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import InsightGenerationRequestSerializer
from .services import generate_insights_for_books


class InsightsStatusView(APIView):
    def get(self, _request):
        return Response({"module": "insights", "status": "ready"})


class InsightGenerationView(APIView):
    def post(self, request):
        serializer = InsightGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = generate_insights_for_books(limit=serializer.validated_data["limit"])
        return Response(
            {"status": "ok", "generated_books": result["generated"], "cached_books": result["skipped"]},
            status=status.HTTP_200_OK,
        )
