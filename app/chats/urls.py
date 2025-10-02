from os import name
from rest_framework.routers import DefaultRouter

from .views import (
    ChatMessageViewset,
    ChatViewset,
)


app_name = "chats"

router = DefaultRouter()
router.register("messages", ChatMessageViewset, basename="chat-messages")
router.register("", ChatViewset)

urlpatterns = router.urls
