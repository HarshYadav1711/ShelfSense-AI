from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .chat_serializers import RagChatHistorySerializer
from .models import RagChatHistory
from .serializers import RagIndexRequestSerializer, RagQuestionRequestSerializer
from .services import answer_question, run_indexing


class RagStatusView(APIView):
    def get(self, _request):
        return Response({"module": "rag", "status": "ready"})


class RagIndexView(APIView):
    def post(self, request):
        serializer = RagIndexRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = run_indexing(limit=serializer.validated_data["limit"])
        return Response({"status": "ok", **result}, status=status.HTTP_200_OK)


class RagQuestionView(APIView):
    def post(self, request):
        serializer = RagQuestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = answer_question(
                question=serializer.validated_data["question"],
                top_k=serializer.validated_data["top_k"],
            )
            return Response(payload, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {
                    "answer": "Unable to answer right now. Please retry after indexing.",
                    "sources": [],
                    "related_books": [],
                    "metadata": {"error": "rag_processing_failed"},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RagHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class RagHistoryView(APIView):
    def get(self, request):
        queryset = RagChatHistory.objects.all()
        paginator = RagHistoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RagChatHistorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
