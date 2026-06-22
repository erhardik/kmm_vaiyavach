from django.urls import path

from apps.requirements.views import (
    RequirementHeaderCreateView,
    RequirementHeaderDeleteView,
    RequirementHeaderListView,
    RequirementHeaderUpdateView,
    RequirementLineCreateView,
    RequirementLineDeleteView,
    RequirementLineListView,
    RequirementLineUpdateView,
    SpecialRequirementCreateView,
    SpecialRequirementDeleteView,
    SpecialRequirementListView,
    SpecialRequirementUpdateView,
)

app_name = "requirements"

urlpatterns = [
    path("", RequirementHeaderListView.as_view(), name="header-list"),
    path("add/", RequirementHeaderCreateView.as_view(), name="header-create"),
    path("<int:pk>/edit/", RequirementHeaderUpdateView.as_view(), name="header-update"),
    path("<int:pk>/delete/", RequirementHeaderDeleteView.as_view(), name="header-delete"),
    path("lines/", RequirementLineListView.as_view(), name="line-list"),
    path("lines/add/", RequirementLineCreateView.as_view(), name="line-create"),
    path("lines/<int:pk>/edit/", RequirementLineUpdateView.as_view(), name="line-update"),
    path("lines/<int:pk>/delete/", RequirementLineDeleteView.as_view(), name="line-delete"),
    path("special/", SpecialRequirementListView.as_view(), name="special-list"),
    path("special/add/", SpecialRequirementCreateView.as_view(), name="special-create"),
    path("special/<int:pk>/edit/", SpecialRequirementUpdateView.as_view(), name="special-update"),
    path("special/<int:pk>/delete/", SpecialRequirementDeleteView.as_view(), name="special-delete"),
]

