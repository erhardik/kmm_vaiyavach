from django.urls import path

from apps.accounts.views import (
    MembershipCreateView,
    MembershipDeleteView,
    MembershipUpdateView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/add/", UserCreateView.as_view(), name="user-create"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user-update"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
    path("users/<int:user_pk>/roles/add/", MembershipCreateView.as_view(), name="membership-create"),
    path("users/<int:user_pk>/roles/<int:pk>/edit/", MembershipUpdateView.as_view(), name="membership-update"),
    path("users/<int:user_pk>/roles/<int:pk>/delete/", MembershipDeleteView.as_view(), name="membership-delete"),
]
