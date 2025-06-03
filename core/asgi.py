# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack # For authentication in WebSockets
import management.routing # Your app's routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Get the standard Django ASGI application to handle HTTP requests
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack( # Handles user authentication for WebSockets
        URLRouter(
            management.routing.websocket_urlpatterns # Points to your app's WebSocket URLs
        )
    ),
})