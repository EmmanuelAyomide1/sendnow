import asyncio
import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from channels.layers import get_channel_layer

from chats.serializers import MessageSerializer
from chats.utils import get_active_users_in_chat, get_all_active_users

from .models import Message


@receiver(post_save, sender=Message)
def send_message_to_chat(sender, instance, **kwargs):
    """
    Sends a message to the chat in real-time.
    """
    try:
        channel_layer = get_channel_layer()
        room_group_name = f"chat_{instance.chat.id}"
        print("room_group_name", room_group_name)
        active_users_in_chat = get_active_users_in_chat(instance.chat.id)
        all_active_users = get_all_active_users()

        users_not_active_in_chat = set(
            map(
                str,
                instance.chat.members.filter()
                .exclude(user__id__in=active_users_in_chat, user__id=instance.sender.id)
                .values_list("user__id", flat=True),
            )
        )
        online_users_not_active_in_chat = users_not_active_in_chat.intersection(
            all_active_users
        )
        print("active_users_in_chat", active_users_in_chat)
        print("all_active_users", all_active_users)
        print("users_not_active_in_chat", users_not_active_in_chat)
        print("online_users_not_active_in_chat", online_users_not_active_in_chat)

        async def send_to_group():
            try:
                message = MessageSerializer(instance).data
                print("message", message)
                await channel_layer.group_send(
                    room_group_name,
                    {"type": "chat_message", "message": message},
                )
                print("sent to group")

                for user_id in online_users_not_active_in_chat:
                    print("sending to user")
                    channel_name = "user_%s" % user_id
                    await channel_layer.group_send(
                        channel_name,
                        {
                            "type": "notify_message",
                            "message": message,
                        },
                    )
            except:
                print("error sending to group")
                import traceback

                traceback.print_exc()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_to_group())
        except RuntimeError:
            asyncio.run(send_to_group())

    except Exception as e:
        print(f"Error in pre_save signal: {e}")
