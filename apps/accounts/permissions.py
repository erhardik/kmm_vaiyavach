from django.contrib.auth.mixins import AccessMixin


def is_systemadmin(user) -> bool:
    return bool(user and user.is_authenticated and user.is_superuser)


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name="KMM Admin").exists()))


def is_viewer(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name="KMM Admin").exists() or user.groups.filter(name="KMM Viewer").exists()))

def is_manager(user) -> bool:
    return bool(user and user.is_authenticated and user.groups.filter(name="KMM Manager").exists())


class RoleRequiredMixin(AccessMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        allowed = {
            "systemadmin": is_systemadmin(user),
            "admin": is_admin(user),
            "viewer": is_viewer(user),
        }
        if not any(allowed.get(role, False) for role in self.allowed_roles):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
