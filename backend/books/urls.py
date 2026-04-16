from django.urls import path

from .views import BooksStatusView

urlpatterns = [
    path("status/", BooksStatusView.as_view(), name="books-status"),
]
