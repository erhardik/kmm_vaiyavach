from django.urls import path

from apps.vendors.views import VendorQuoteCreateView, VendorQuoteDeleteView, VendorQuoteListView, VendorQuoteUpdateView

app_name = "vendors"

urlpatterns = [
    path("", VendorQuoteListView.as_view(), name="quote-list"),
    path("add/", VendorQuoteCreateView.as_view(), name="quote-create"),
    path("<int:pk>/edit/", VendorQuoteUpdateView.as_view(), name="quote-update"),
    path("<int:pk>/delete/", VendorQuoteDeleteView.as_view(), name="quote-delete"),
]

