from django.urls import re_path

from users.cosumers import ChatConsumer, UserConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<chat_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$",
        ChatConsumer.as_asgi(),
    ),
    re_path(r"ws/notifications/$", UserConsumer.as_asgi()),
]
