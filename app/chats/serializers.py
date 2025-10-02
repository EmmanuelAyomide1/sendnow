from os import read
from rest_framework import serializers

from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, format="hex_verbose")
    chat_id = serializers.UUIDField(
        source="chat.id", read_only=True, format="hex_verbose"
    )
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    sender_info = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"
        extra_kwargs = {
            "is_deleted": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "chat": {"write_only": True},
        }

    def get_sender_info(self, obj):
        sender = obj.sender
        return {
            "id": str(sender.id),
            "profile_picture": (
                sender.profile_picture.url if sender.profile_picture else None
            ),
            "name": sender.name,
        }


class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "type", "name", "profile_picture", "last_message"]

    def get_profile_picture(self, obj):
        if obj.type == Chat.ChatTypes.individual:
            other_user = (
                obj.members.exclude(user=self.context["request"].user).first().user
            )
            profile_picture = other_user.profile_picture
        else:
            profile_picture = obj.profile_picture

        if not profile_picture:
            return None
        return profile_picture.url

    def get_name(self, obj):
        if obj.type == Chat.ChatTypes.individual:
            other_user = (
                obj.members.exclude(user=self.context["request"].user).first().user
            )
            return other_user.name
        return obj.name

    def get_last_message(self, obj):
        last_message = (
            obj.messages.filter(is_deleted=False).order_by("-created_at").first()
        )
        if last_message:
            return MessageSerializer(last_message).data
        return None


class CreatePrivateChatSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
