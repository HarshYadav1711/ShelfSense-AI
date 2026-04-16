from django.urls import path

from .views import (
    BookDetailView,
    BookListView,
    BooksStatusView,
    RelatedBooksView,
    UploadProcessBooksView,
    UploadProcessStatusView,
)

urlpatterns = [
    path("status/", BooksStatusView.as_view(), name="books-status"),
    path("", BookListView.as_view(), name="books-list"),
    path("upload-process/", UploadProcessBooksView.as_view(), name="books-upload-process"),
    path("upload-process/<int:job_id>/", UploadProcessStatusView.as_view(), name="books-upload-process-status"),
    path("<int:book_id>/", BookDetailView.as_view(), name="books-detail"),
    path("<int:book_id>/related/", RelatedBooksView.as_view(), name="books-related"),
]
