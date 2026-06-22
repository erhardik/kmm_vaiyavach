from django.urls import path

from apps.sponsorship.views import (
    SponsorMaterialReceiptCreateView,
    SponsorMaterialReceiptDeleteView,
    SponsorMaterialReceiptListView,
    SponsorMaterialReceiptUpdateView,
    SponsorshipCommitmentCreateView,
    SponsorshipCommitmentDeleteView,
    SponsorshipCommitmentListView,
    SponsorshipCommitmentUpdateView,
)

app_name = "sponsorship"

urlpatterns = [
    path("", SponsorshipCommitmentListView.as_view(), name="commitment-list"),
    path("add/", SponsorshipCommitmentCreateView.as_view(), name="commitment-create"),
    path("<int:pk>/edit/", SponsorshipCommitmentUpdateView.as_view(), name="commitment-update"),
    path("<int:pk>/delete/", SponsorshipCommitmentDeleteView.as_view(), name="commitment-delete"),
    path("receipts/", SponsorMaterialReceiptListView.as_view(), name="receipt-list"),
    path("receipts/add/", SponsorMaterialReceiptCreateView.as_view(), name="receipt-create"),
    path("receipts/<int:pk>/edit/", SponsorMaterialReceiptUpdateView.as_view(), name="receipt-update"),
    path("receipts/<int:pk>/delete/", SponsorMaterialReceiptDeleteView.as_view(), name="receipt-delete"),
]

