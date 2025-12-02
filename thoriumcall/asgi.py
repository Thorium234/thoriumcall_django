import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import thoriumcall.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "thoriumcall.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(thoriumcall.routing.websocket_urlpatterns),
    }
)
