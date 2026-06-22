from django.urls import path

from apps.dashboard.views import DashboardHomeView, ItemControlCenterView

app_name = "dashboard"

urlpatterns = [
    path("", ItemControlCenterView.as_view(), name="item_control_center"),
    path("home/", DashboardHomeView.as_view(), name="home"),
]

