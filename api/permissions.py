from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import AccountTier


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
    

class CanCreateTempLinks(permissions.BasePermission):
    """
    Checks if user's account tier allows for creating
    temporary links.
    """
    
    message = _(("User's account tier does not allow " +
        "for temporary links creation."))
    
    def has_permission(self, request, view):
        account_tier = getattr(
            request.user, 
            'account_tier', 
            None
        )
        if account_tier:
            return account_tier.can_generate_temp_link
        return False