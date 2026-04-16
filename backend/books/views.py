from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.services import run_book_ingestion
from insights.services import generate_insights_for_books
from rag.services import run_indexing

from .models import Book, BookInsight
from .serializers import BookDetailSerializer, BookListSerializer, UploadProcessRequestSerializer


class BooksStatusView(APIView):
    def get(self, _request):
        return Response({"module": "books", "status": "ready"})


class BookPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class BookListView(APIView):
    def get(self, request):
        queryset = Book.objects.all().order_by("title")
        search = request.query_params.get("search")
        min_rating = request.query_params.get("min_rating")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(author__icontains=search)
                | Q(description__icontains=search)
            )

        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                return Response(
                    {"message": "Invalid min_rating value. Use a numeric value."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        paginator = BookPagination()
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = BookListSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)


class BookDetailView(APIView):
    def get(self, _request, book_id: int):
        try:
            book = Book.objects.prefetch_related("insights").get(id=book_id)
        except Book.DoesNotExist:
            return Response({"message": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(BookDetailSerializer(book).data)


class RelatedBooksView(APIView):
    def get(self, _request, book_id: int):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"message": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        genre_insight = (
            BookInsight.objects.filter(book=book, insight_type="genre").values_list("content", flat=True).first()
        )

        candidates = Book.objects.exclude(id=book.id)
        if genre_insight:
            related_ids = (
                BookInsight.objects.filter(insight_type="genre", content__icontains=genre_insight[:30])
                .exclude(book_id=book.id)
                .values_list("book_id", flat=True)
            )
            candidates = candidates.filter(id__in=related_ids)

        if book.rating is not None:
            candidates = candidates.order_by("-rating", "title")
        else:
            candidates = candidates.order_by("title")

        serializer = BookListSerializer(candidates[:5], many=True)
        return Response({"book_id": book.id, "results": serializer.data})


class UploadProcessBooksView(APIView):
    def post(self, request):
        serializer = UploadProcessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        limit = serializer.validated_data["limit"]

        ingestion_run = run_book_ingestion(limit=limit)
        insight_stats = generate_insights_for_books(limit=limit)
        index_stats = run_indexing(limit=limit * 4)

        return Response(
            {
                "status": "ok",
                "ingestion": {
                    "run_id": ingestion_run.id,
                    "status": ingestion_run.status,
                    "processed_count": ingestion_run.processed_count,
                    "failed_count": ingestion_run.failed_count,
                },
                "insights": insight_stats,
                "indexing": index_stats,
            },
            status=status.HTTP_202_ACCEPTED,
        )
