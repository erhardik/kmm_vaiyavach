from django.urls import path

from apps.dashboard.views import (
    ChaturmasDashboardDataView,
    ChaturmasDashboardView,
    DashboardHomeView,
    FeedbackDeleteView,
    FeedbackListView,
    ItemControlCenterView,
)

app_name = "dashboard"

urlpatterns = [
    path("", ItemControlCenterView.as_view(), name="item_control_center"),
    path("home/", DashboardHomeView.as_view(), name="home"),
    path("chaturmas/", ChaturmasDashboardView.as_view(), name="chaturmas-dashboard"),
    path("api/data/", ChaturmasDashboardDataView.as_view(), name="dashboard-api-data"),
    path("feedback/", FeedbackListView.as_view(), name="feedback-list"),
    path("feedback/<int:pk>/delete/", FeedbackDeleteView.as_view(), name="feedback-delete"),
]

