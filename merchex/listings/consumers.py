"""
WebSocket Consumer pour les cotes en temps réel
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Match, Cote

logger = logging.getLogger(__name__)


class CotesConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour recevoir les mises à jour de cotes en temps réel

    URLs acceptées :
    - ws://domain/ws/cotes/ → Toutes les cotes
    - ws://domain/ws/cotes/123/ → Cotes du match 123
    """

    async def connect(self):
        """Connexion au WebSocket"""
        # Récupérer le match_id depuis l'URL (optionnel)
        self.match_id = self.scope['url_route']['kwargs'].get('match_id', 'all')

        if self.match_id == 'all':
            # S'abonner à tous les matchs
            self.room_group_name = 'cotes_all'
        else:
            # S'abonner à un match spécifique
            self.room_group_name = f'cotes_{self.match_id}'

        # Rejoindre le groupe de room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accepter la connexion WebSocket
        await self.accept()

        logger.info(f"[WEBSOCKET] Client connecté au groupe {self.room_group_name}")

        # Envoyer les cotes actuelles dès la connexion
        await self.send_current_cotes()

    async def disconnect(self, close_code):
        """Déconnexion du WebSocket"""
        # Quitter le groupe de room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"[WEBSOCKET] Client déconnecté du groupe {self.room_group_name}")

    async def receive(self, text_data):
        """
        Recevoir des messages du client
        (Optionnel - pour l'instant on ne fait que broadcaster)
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'ping':
                # Répondre au ping du client
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))

        except json.JSONDecodeError:
            logger.error("[WEBSOCKET] Message JSON invalide reçu")

    async def send_current_cotes(self):
        """Envoyer les cotes actuelles au client à la connexion"""
        if self.match_id != 'all':
            # Envoyer les cotes d'un match spécifique
            cotes_data = await self.get_cotes_for_match(self.match_id)
            if cotes_data:
                await self.send(text_data=json.dumps({
                    'type': 'cotes_update',
                    'data': cotes_data
                }))
        else:
            # Envoyer les cotes de tous les matchs à venir
            all_cotes = await self.get_all_cotes()
            await self.send(text_data=json.dumps({
                'type': 'cotes_initial',
                'data': all_cotes
            }))

    @database_sync_to_async
    def get_cotes_for_match(self, match_id):
        """Récupérer les cotes d'un match depuis la base de données"""
        try:
            cote = Cote.objects.select_related('match').get(match_id=match_id)
            return {
                'match_id': match_id,
                'cote1': float(cote.cote1),
                'cote2': float(cote.cote2),
                'coteN': float(cote.coteN),
                'last_updated': cote.last_updated.isoformat(),
                'paris_count': cote.paris_count_since_last_update,
                'match': {
                    'equipe1': cote.match.equipe1,
                    'equipe2': cote.match.equipe2,
                    'date': str(cote.match.date),
                    'heure': str(cote.match.heure)
                }
            }
        except Cote.DoesNotExist:
            logger.warning(f"[WEBSOCKET] Cote non trouvée pour match {match_id}")
            return None

    @database_sync_to_async
    def get_all_cotes(self):
        """Récupérer toutes les cotes des matchs à venir"""
        from django.utils import timezone
        import pytz

        # Date actuelle
        paris_tz = pytz.timezone('Europe/Paris')
        now_paris = timezone.now().astimezone(paris_tz)
        today = now_paris.date()

        # Matchs à venir uniquement
        cotes = Cote.objects.select_related('match').filter(
            match__date__gte=today
        )[:50]  # Limiter à 50 pour éviter trop de données

        return [{
            'match_id': cote.match.id,
            'cote1': float(cote.cote1),
            'cote2': float(cote.cote2),
            'coteN': float(cote.coteN),
            'last_updated': cote.last_updated.isoformat(),
            'match': {
                'equipe1': cote.match.equipe1,
                'equipe2': cote.match.equipe2,
                'date': str(cote.match.date),
                'heure': str(cote.match.heure)
            }
        } for cote in cotes]

    async def cotes_update(self, event):
        """
        Recevoir une mise à jour de cotes depuis le channel layer
        et la transmettre au client WebSocket
        """
        # Envoyer la mise à jour au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'cotes_update',
            'data': event['data']
        }))

        logger.info(f"[WEBSOCKET] Mise à jour envoyée pour match {event['data'].get('match_id')}")
