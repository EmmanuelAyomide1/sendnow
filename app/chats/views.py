from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsChatMember
from .models import Chat, Message
from .serializers import ChatSerializer, CreatePrivateChatSerializer, MessageSerializer

# Create your views here.


class ChatViewset(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]
    lookup_field = "id"
    lookup_url_kwarg = "chat_id"
    serializer_class = ChatSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return (
                super()
                .get_queryset()
                .filter(members__user=self.request.user)
                .order_by("-created_at")
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="user",
        serializer_class=CreatePrivateChatSerializer,
    )
    def get_conversation_id(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        user = get_object_or_404(get_user_model(), id=user_id)

        chat = (
            Chat.objects.filter(members__user__in=[request.user, user])
            .annotate(member_count=Count("members"))
            .filter(member_count=2)
            .first()
        )
        if not chat:
            chat = Chat.objects.create(type=Chat.ChatTypes.individual)
            chat.members.create(user=request.user)
            chat.members.create(user=user)

        return Response(
            {
                "data": chat.id,
                "message": "Conversation Id retrieved succesfully",
            }
        )


class ChatMessageViewset(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "delete"]
    serializer_class = MessageSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsChatMember()]
        return super().get_permissions()
