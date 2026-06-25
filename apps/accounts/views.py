from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.forms import EventMembershipForm, SystemUserCreateForm, SystemUserUpdateForm, UserProfileForm
from apps.accounts.models import EventMembership, UserProfile
from apps.accounts.permissions import RoleRequiredMixin
from apps.masters.models import Event


User = get_user_model()


class SystemAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("systemadmin",)


def _role_summary(user):
    memberships = list(
        user.event_memberships.select_related("event").filter(is_active=True).order_by("-is_primary", "event__start_date", "event__name")
    )
    if not memberships:
        return "No event roles"
    return ", ".join(f"{membership.event.name}: {membership.get_role_display()}" for membership in memberships)


class UserListView(SystemAdminRequiredMixin, TemplateView):
    template_name = "common/list.html"

    def get_queryset(self):
        qs = User.objects.all().select_related("profile").prefetch_related("event_memberships__event").order_by("username")
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(profile__mobile__icontains=search)
                | Q(event_memberships__event__name__icontains=search)
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = self.get_queryset()
        rows = []
        for user in users:
            profile = getattr(user, "profile", None)
            rows.append(
                {
                    "object": user,
                    "cells": [
                        user.username,
                        user.email,
                        profile.mobile if profile else "",
                        "Yes" if user.is_staff else "No",
                        "Yes" if user.is_superuser else "No",
                        _role_summary(user),
                    ],
                    "edit_url": reverse("accounts:user-update", kwargs={"pk": user.pk}),
                    "delete_url": reverse("accounts:user-delete", kwargs={"pk": user.pk}),
                }
            )
        context["page_title"] = "User Management"
        context["page_subtitle"] = "Create system accounts and assign event-level access roles."
        context["table_headers"] = ["Username", "Email", "Mobile", "Staff", "Superuser", "Roles"]
        context["table_rows"] = rows
        context["can_add"] = True
        context["can_change"] = True
        context["can_delete"] = True
        context["create_url"] = reverse_lazy("accounts:user-create")
        return context


class UserCreateView(SystemAdminRequiredMixin, View):
    template_name = "accounts/user_form.html"

    def get(self, request, *args, **kwargs):
        return self._render(request, SystemUserCreateForm(), UserProfileForm())

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_form = SystemUserCreateForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "User created successfully.")
            return redirect("accounts:user-update", pk=user.pk)
        return self._render(request, user_form, profile_form)

    def _render(self, request, user_form, profile_form):
        return render(
            request,
            self.template_name,
            {
                "page_title": "Create User",
                "page_subtitle": "Add a new system user and basic profile details.",
                "list_url": reverse_lazy("accounts:user-list"),
                "user_form": user_form,
                "profile_form": profile_form,
                "memberships": None,
                "is_create": True,
            },
        )


class UserUpdateView(SystemAdminRequiredMixin, View):
    template_name = "accounts/user_form.html"

    def _get_user(self, pk):
        return get_object_or_404(User.objects.select_related("profile"), pk=pk)

    def get(self, request, pk, *args, **kwargs):
        user = self._get_user(pk)
        return self._render(request, user, SystemUserUpdateForm(instance=user), UserProfileForm(instance=getattr(user, "profile", None)))

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        user = self._get_user(pk)
        user_form = SystemUserUpdateForm(request.POST, instance=user)
        profile_instance = getattr(user, "profile", None)
        profile_form = UserProfileForm(request.POST, instance=profile_instance)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "User updated successfully.")
            return redirect("accounts:user-update", pk=user.pk)
        return self._render(request, user, user_form, profile_form)

    def _render(self, request, user, user_form, profile_form):
        memberships = user.event_memberships.select_related("event").order_by("-is_primary", "event__start_date", "event__name")
        return render(
            request,
            self.template_name,
            {
                "page_title": f"Edit User: {user.username}",
                "page_subtitle": "Manage login details, profile data, and event roles.",
                "list_url": reverse_lazy("accounts:user-list"),
                "user": user,
                "user_form": user_form,
                "profile_form": profile_form,
                "memberships": memberships,
                "membership_create_url": reverse("accounts:membership-create", kwargs={"user_pk": user.pk}),
                "user_delete_url": reverse("accounts:user-delete", kwargs={"pk": user.pk}),
                "is_create": False,
            },
        )


class UserDeleteView(SystemAdminRequiredMixin, View):
    template_name = "common/confirm_delete.html"

    def get(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        return render(
            request,
            self.template_name,
            {
                "object": user,
                "page_title": "Delete User",
                "list_url": reverse_lazy("accounts:user-list"),
            },
        )

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("accounts:user-list")


class MembershipCreateView(SystemAdminRequiredMixin, View):
    template_name = "accounts/membership_form.html"

    def get_user(self, user_pk):
        return get_object_or_404(User, pk=user_pk)

    def get(self, request, user_pk, *args, **kwargs):
        user = self.get_user(user_pk)
        form = EventMembershipForm(initial={"is_active": True})
        return self._render(request, user, form)

    @transaction.atomic
    def post(self, request, user_pk, *args, **kwargs):
        user = self.get_user(user_pk)
        form = EventMembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.user = user
            membership.save()
            messages.success(request, "Role saved successfully.")
            return redirect("accounts:user-update", pk=user.pk)
        return self._render(request, user, form)

    def _render(self, request, user, form):
        return render(
            request,
            self.template_name,
            {
                "page_title": f"Add Role for {user.username}",
                "page_subtitle": "Assign this user to an event and role.",
                "list_url": reverse("accounts:user-update", kwargs={"pk": user.pk}),
                "form": form,
                "user": user,
            },
        )


class MembershipUpdateView(SystemAdminRequiredMixin, View):
    template_name = "accounts/membership_form.html"

    def get_object(self, user_pk, pk):
        return get_object_or_404(EventMembership, pk=pk, user_id=user_pk)

    def get(self, request, user_pk, pk, *args, **kwargs):
        membership = self.get_object(user_pk, pk)
        form = EventMembershipForm(instance=membership)
        return self._render(request, membership.user, form, membership)

    @transaction.atomic
    def post(self, request, user_pk, pk, *args, **kwargs):
        membership = self.get_object(user_pk, pk)
        form = EventMembershipForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, "Role updated successfully.")
            return redirect("accounts:user-update", pk=membership.user_id)
        return self._render(request, membership.user, form, membership)

    def _render(self, request, user, form, membership=None):
        return render(
            request,
            self.template_name,
            {
                "page_title": f"Edit Role for {user.username}",
                "page_subtitle": "Update the event access for this user.",
                "list_url": reverse("accounts:user-update", kwargs={"pk": user.pk}),
                "form": form,
                "user": user,
                "membership": membership,
            },
        )


class MembershipDeleteView(SystemAdminRequiredMixin, View):
    template_name = "common/confirm_delete.html"

    def get_object(self, user_pk, pk):
        return get_object_or_404(EventMembership, pk=pk, user_id=user_pk)

    def get(self, request, user_pk, pk, *args, **kwargs):
        membership = self.get_object(user_pk, pk)
        return render(
            request,
            self.template_name,
            {
                "object": membership,
                "page_title": "Delete Role",
                "list_url": reverse("accounts:user-update", kwargs={"pk": membership.user_id}),
            },
        )

    def post(self, request, user_pk, pk, *args, **kwargs):
        membership = self.get_object(user_pk, pk)
        user_pk_value = membership.user_id
        membership.delete()
        messages.success(request, "Role deleted successfully.")
        return redirect("accounts:user-update", pk=user_pk_value)
