from django.conf import settings
from django.conf.urls.i18n import set_language
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.accounts.forms import BootstrapAuthenticationForm
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
    path("", include("apps.dashboard.urls")),
    path("masters/", include("apps.masters.urls")),
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
