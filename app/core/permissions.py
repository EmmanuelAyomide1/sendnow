from rest_framework.permissions import IsAuthenticated, BasePermission

from django.contrib.auth import get_user_model


class IsAuthenticationAndRegistered(IsAuthenticated):
    message = "Only Registered users can access this view."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(request.user.name)


class IsOwner(BasePermission):
    """Allows only owners of an object to edit it."""

    message = "You do not have the permission to modify this object."

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, get_user_model()) and obj == request.user:
            return True
        elif isinstance(obj, get_user_model()) is False and obj.sender == request.user:
            return True
        return False
