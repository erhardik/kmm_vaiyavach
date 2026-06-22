from apps.accounts.permissions import is_admin, is_systemadmin, is_viewer


def can_view(user) -> bool:
    return is_viewer(user)


def can_edit(user) -> bool:
    return is_admin(user)


def can_manage(user) -> bool:
    return is_systemadmin(user)
