from django.urls import path

from apps.distribution.views import (
    DistributionBatchCreateView,
    DistributionBatchDeleteView,
    DistributionBatchListView,
    DistributionBatchUpdateView,
    DistributionLineCreateView,
    DistributionLineDeleteView,
    DistributionLineListView,
    DistributionLineUpdateView,
)

app_name = "distribution"

urlpatterns = [
    path("batches/", DistributionBatchListView.as_view(), name="batch-list"),
    path("batches/add/", DistributionBatchCreateView.as_view(), name="batch-create"),
    path("batches/<int:pk>/edit/", DistributionBatchUpdateView.as_view(), name="batch-update"),
    path("batches/<int:pk>/delete/", DistributionBatchDeleteView.as_view(), name="batch-delete"),
    path("lines/", DistributionLineListView.as_view(), name="line-list"),
    path("lines/add/", DistributionLineCreateView.as_view(), name="line-create"),
    path("lines/<int:pk>/edit/", DistributionLineUpdateView.as_view(), name="line-update"),
    path("lines/<int:pk>/delete/", DistributionLineDeleteView.as_view(), name="line-delete"),
]

