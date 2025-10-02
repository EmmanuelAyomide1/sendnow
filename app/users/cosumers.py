import json

from django.core.cache import cache
from django.utils import timezone

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chats.models import ChatParticipant


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat_id = self.scope["url_route"]["kwargs"].get("chat_id")

        print("User:", self.user.is_authenticated)
        print("chat", self.chat_id)
        if (
            not self.user.is_authenticated
            or not self.chat_id
            or not await self.handle_user_join_chat()
        ):
            await self.close()
            return
        self.room_group_name = "chat_%s" % self.chat_id
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.heartbeat()
        await self.accept()

    async def disconnect(self, close_code):
        # if self.active_chat:
        #     self.active_chat.is_active = False

        if self.chat_id and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            cache.delete(self.user_cache_key)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        type = data.get("type")

        if type == "ping":
            await self.heartbeat()
            await self.send(text_data=json.dumps({"type": "pong"}))

        elif type == "typing":
            pass
        elif type == "stop_typing":
            pass
        elif type == "read_message":
            pass
        elif type == "delete_message":
            pass
        elif type == "edit_message":
            pass

    @database_sync_to_async
    def heartbeat(self):
        print("heartbeat")
        self.user_cache_key = "%s:active_users:%s" % (
            self.room_group_name,
            self.user.id,
        )
        print("cache_key", self.user_cache_key)
        cache.set(self.user_cache_key, self.user.id, 20)
        print("set")

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def handle_user_join_chat(self):
        participant = ChatParticipant.objects.filter(
            chat_id=self.chat_id, user=self.user
        ).first()

        print("participant", participant)

        if not participant:
            return False

        return True


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        print("User:", self.user)
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join user to channel_id
        self.room_group_name = "user_%s" % self.user.id

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        if data.get("type") == "ping":
            await self.heartbeat()
            await self.send(text_data=json.dumps({"type": "pong"}))

    @database_sync_to_async
    def heartbeat(self):
        cache.set("last_seen_:%s" % self.user.id, timezone.now(), 30)

    async def notify_message(self, event):
        message = event.get("message")
        await self.send(text_data=json.dumps({"message": message}))
