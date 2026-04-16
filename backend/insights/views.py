from rest_framework.response import Response
from rest_framework.views import APIView


class InsightsStatusView(APIView):
    def get(self, _request):
        return Response({"module": "insights", "status": "ready"})
