from django.urls import path

from .views import IngestionRunView, IngestionStatusView

urlpatterns = [
    path("status/", IngestionStatusView.as_view(), name="ingestion-status"),
    path("run/", IngestionRunView.as_view(), name="ingestion-run"),
]
