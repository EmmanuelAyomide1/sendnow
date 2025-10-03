"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.staging")

from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application


asgi_appication = get_asgi_application()


def get_application():

    from .middleware import JWTAuthMiddleware
    from .routing import websocket_urlpatterns

    return ProtocolTypeRouter(
        {
            "http": asgi_appication,
            "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
        }
    )


application = get_application()
