from rest_framework.permissions import IsAuthenticated


class IsAuthenticationAndRegistered(IsAuthenticated):
    message = 'Only Registered users can access this view.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(request.user.name)
