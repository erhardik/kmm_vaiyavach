from django.urls import path

from apps.funds.views import (
    DonationCreateView,
    DonationDeleteView,
    DonationListView,
    DonationUpdateView,
    FundTransactionCreateView,
    FundTransactionDeleteView,
    FundTransactionListView,
    FundTransactionUpdateView,
)

app_name = "funds"

urlpatterns = [
    path("donations/", DonationListView.as_view(), name="donation-list"),
    path("donations/add/", DonationCreateView.as_view(), name="donation-create"),
    path("donations/<int:pk>/edit/", DonationUpdateView.as_view(), name="donation-update"),
    path("donations/<int:pk>/delete/", DonationDeleteView.as_view(), name="donation-delete"),
    path("transactions/", FundTransactionListView.as_view(), name="transaction-list"),
    path("transactions/add/", FundTransactionCreateView.as_view(), name="transaction-create"),
    path("transactions/<int:pk>/edit/", FundTransactionUpdateView.as_view(), name="transaction-update"),
    path("transactions/<int:pk>/delete/", FundTransactionDeleteView.as_view(), name="transaction-delete"),
]

