from django.urls import path

from apps.auditlog.views import ActivityLogListView

app_name = "auditlog"

urlpatterns = [
    path("", ActivityLogListView.as_view(), name="activity-list"),
]
