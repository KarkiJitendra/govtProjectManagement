# core_app/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # The URL will identify the user you want to chat with
    re_path(r'ws/chat/(?P<other_username>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),

]