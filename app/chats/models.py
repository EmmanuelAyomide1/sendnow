import uuid

from django.contrib.auth import get_user_model
from django.db import models

from core.models import TimeStampedModel


# Create your models here.


class Chat(TimeStampedModel):

    class ChatTypes(models.TextChoices):
        group = "Group", "G"
        individual = "Individual", "I"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    type = models.CharField(
        choices=ChatTypes.choices, default=ChatTypes.individual, max_length=10
    )
    profile_picture = models.ImageField(
        upload_to="chats/profile", null=True, blank=True
    )
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        related_name="created_chats",
        null=True,
        blank=True,
    )


class ChatParticipant(TimeStampedModel):

    class Roles(models.TextChoices):
        admin = "Admin", "A"
        member = "Member", "M"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="chats"
    )
    left_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.member)


class Message(TimeStampedModel):

    class MessageType(models.TextChoices):
        audio = "Audio", "A"
        video = "Video", "V"
        image = "Image", "I"
        document = "Document", "D"
        text = "Text", "T"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    type = models.CharField(
        choices=MessageType.choices, default=MessageType.text, max_length=10
    )
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_forwarded = models.BooleanField(default=False)
    conversation = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="messages"
    )


class MessageStatus(TimeStampedModel):

    class Status(models.TextChoices):
        delivered = "Delivered", "D"
        read = "Read", "R"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="message_info"
    )
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="users_reached"
    )
    status = models.CharField(choices=Status.choices, default=Status.delivered)


class MessageMedia(TimeStampedModel):

    class MediaType(models.TextChoices):
        audio = "Audio", "A"
        video = "Video", "V"
        image = "Image", "I"
        document = "Document", "D"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="media")
    type = models.CharField(choices=MediaType.choices, max_length=10)
    file = models.FileField(upload_to="messages/media")
