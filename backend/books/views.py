from rest_framework.response import Response
from rest_framework.views import APIView


class BooksStatusView(APIView):
    def get(self, _request):
        return Response({"module": "books", "status": "ready"})
