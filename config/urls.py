from django.conf import settings
from django.conf.urls.i18n import set_language
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from django.shortcuts import redirect

from apps.accounts.forms import BootstrapAuthenticationForm
from apps.dashboard.views import PublicLandingView
from apps.masters.models import Event
from apps.requirements.views import PublicRequirementListView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=BootstrapAuthenticationForm,
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("i18n/setlang/", set_language, name="set_language"),
    path("", PublicLandingView.as_view(), name="public-landing"),
    path("requests/", PublicRequirementListView.as_view(), name="public-requests"),
    path("form", lambda r: redirect("requirements:public-collect", event_token=Event.objects.filter(is_current=True, is_active=True).first().public_form_token) if Event.objects.filter(is_current=True, is_active=True).first() else redirect("public-landing")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("masters/", include("apps.masters.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("requirements/", include("apps.requirements.urls")),
    path("sponsorship/", include("apps.sponsorship.urls")),
    path("vendors/", include("apps.vendors.urls")),
    path("procurement/", include("apps.procurement.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("distribution/", include("apps.distribution.urls")),
    path("funds/", include("apps.funds.urls")),
    path("reports/", include("apps.reports.urls")),
    path("auditlog/", include("apps.auditlog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
