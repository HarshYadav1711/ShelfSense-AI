from django.urls import path

from .views import InsightGenerationView, InsightsStatusView

urlpatterns = [
    path("status/", InsightsStatusView.as_view(), name="insights-status"),
    path("generate/", InsightGenerationView.as_view(), name="insights-generate"),
]
