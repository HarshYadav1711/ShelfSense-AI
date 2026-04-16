from rest_framework.response import Response
from rest_framework.views import APIView


class IngestionStatusView(APIView):
    def get(self, _request):
        return Response({"module": "ingestion", "status": "ready"})
