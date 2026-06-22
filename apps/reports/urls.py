from django.urls import path

from apps.reports.views import AnalyticsView, FundLedgerExportView, InventoryLedgerExportView, ItemControlExportView, ReportHomeView, RequirementExportView, SponsorshipExportView

app_name = "reports"

urlpatterns = [
    path("", ReportHomeView.as_view(), name="report-home"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("item-control/export/", ItemControlExportView.as_view(), name="item-control-export"),
    path("inventory/export/", InventoryLedgerExportView.as_view(), name="inventory-export"),
    path("funds/export/", FundLedgerExportView.as_view(), name="fund-export"),
    path("requirements/export/", RequirementExportView.as_view(), name="requirement-export"),
    path("sponsorship/export/", SponsorshipExportView.as_view(), name="sponsorship-export"),
]
