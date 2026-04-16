from django.urls import path

from .views import RagIndexView, RagQuestionView, RagStatusView

urlpatterns = [
    path("status/", RagStatusView.as_view(), name="rag-status"),
    path("index/", RagIndexView.as_view(), name="rag-index"),
    path("ask/", RagQuestionView.as_view(), name="rag-ask"),
]
