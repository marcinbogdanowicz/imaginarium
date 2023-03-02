from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsOwner(permissions.BasePermission):
    """
    Requires user to be the owner of the object he tries to access.
    Requires user to be the user instance in case of User model.
    """

    message = _("Attempt to access another user's data.")

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner = getattr(obj, 'owner', None)
        return (obj == user or owner == user)