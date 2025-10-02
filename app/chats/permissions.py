from rest_framework.permissions import BasePermission

from core.permissions import IsAuthenticationAndRegistered
from .models import Chat


class IsChatMember(IsAuthenticationAndRegistered, BasePermission):
    message = "Only Members of this chat can access this view."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        chat_id = request.data.get("chat")
        return Chat.objects.filter(id=chat_id, members__user=request.user).exists()
