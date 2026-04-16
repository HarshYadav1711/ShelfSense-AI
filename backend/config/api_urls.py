from django.urls import include, path

urlpatterns = [
    path("books/", include("books.urls")),
    path("ingestion/", include("ingestion.urls")),
    path("insights/", include("insights.urls")),
    path("rag/", include("rag.urls")),
]
