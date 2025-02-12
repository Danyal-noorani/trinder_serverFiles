from django.urls import path
from .consumers import ChatConsumer
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

websocket_urlpatterns = [
    path("ws/chat/<str:roomId>/", ChatConsumer.as_asgi()),
]
