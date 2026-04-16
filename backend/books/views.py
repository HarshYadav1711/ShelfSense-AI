from django.db.models import Q
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.pipeline import launch_pipeline_job
from ingestion.models import PipelineJob
from ingestion.serializers import PipelineJobSerializer
from rag.services import related_book_ids_via_embeddings

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


def _genre_based_related_books(book: Book) -> list[Book]:
    """Legacy related list: genre substring overlap, then rating/title ordering."""
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

    return list(candidates[:5])


class RelatedBooksView(APIView):
    """
    Related titles for a book.

    Primary: embed the book's description and query Chroma for similar indexed
    chunks; return up to five **distinct** other books ranked by best chunk
    similarity. Fallback: genre-overlap heuristic (existing behavior) when
    embeddings are unavailable or yield no candidates.
    """

    def get(self, _request, book_id: int):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"message": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        related_ids = related_book_ids_via_embeddings(book, limit=5)
        if related_ids:
            rows = {b.id: b for b in Book.objects.filter(id__in=related_ids)}
            ordered = [rows[i] for i in related_ids if i in rows]
            if ordered:
                serializer = BookListSerializer(ordered, many=True)
                return Response({"book_id": book.id, "results": serializer.data})

        serializer = BookListSerializer(_genre_based_related_books(book), many=True)
        return Response({"book_id": book.id, "results": serializer.data})


class UploadProcessBooksView(APIView):
    def post(self, request):
        serializer = UploadProcessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        limit = serializer.validated_data["limit"]
        max_pages = serializer.validated_data["max_pages"]
        job = launch_pipeline_job(limit=limit, max_pages=max_pages)

        return Response(
            {
                "status": "ok",
                "job": PipelineJobSerializer(job).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class UploadProcessStatusView(APIView):
    def get(self, _request, job_id: int):
        try:
            job = PipelineJob.objects.get(id=job_id)
        except PipelineJob.DoesNotExist:
            return Response({"message": "Pipeline job not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PipelineJobSerializer(job).data, status=status.HTTP_200_OK)
