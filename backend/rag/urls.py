from django.urls import path

from .views import RagStatusView

urlpatterns = [
    path("status/", RagStatusView.as_view(), name="rag-status"),
]
