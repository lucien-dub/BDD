"""
WebSocket URL routing pour les cotes en temps réel
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket pour tous les matchs
    re_path(r'ws/cotes/$', consumers.CotesConsumer.as_asgi()),

    # WebSocket pour un match spécifique
    re_path(r'ws/cotes/(?P<match_id>\w+)/$', consumers.CotesConsumer.as_asgi()),
]
