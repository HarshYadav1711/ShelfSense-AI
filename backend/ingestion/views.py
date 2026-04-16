from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import IngestionRunRequestSerializer, IngestionRunSerializer
from .services import run_book_ingestion


class IngestionStatusView(APIView):
    def get(self, _request):
        return Response({"module": "ingestion", "status": "ready"})


class IngestionRunView(APIView):
    def post(self, request):
        serializer = IngestionRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        run = run_book_ingestion(limit=serializer.validated_data["limit"])
        return Response(IngestionRunSerializer(run).data, status=status.HTTP_202_ACCEPTED)
