from rest_framework.response import Response
from rest_framework.views import APIView


class RagStatusView(APIView):
    def get(self, _request):
        return Response({"module": "rag", "status": "ready"})
