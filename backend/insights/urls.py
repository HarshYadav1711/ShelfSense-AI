from django.urls import path

from .views import InsightsStatusView

urlpatterns = [
    path("status/", InsightsStatusView.as_view(), name="insights-status"),
]
