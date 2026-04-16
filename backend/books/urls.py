from django.urls import path

from .views import (
    BookDetailView,
    BookListView,
    BooksStatusView,
    RelatedBooksView,
    UploadProcessBooksView,
)

urlpatterns = [
    path("status/", BooksStatusView.as_view(), name="books-status"),
    path("", BookListView.as_view(), name="books-list"),
    path("upload-process/", UploadProcessBooksView.as_view(), name="books-upload-process"),
    path("<int:book_id>/", BookDetailView.as_view(), name="books-detail"),
    path("<int:book_id>/related/", RelatedBooksView.as_view(), name="books-related"),
]
