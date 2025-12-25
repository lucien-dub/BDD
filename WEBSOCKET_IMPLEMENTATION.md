# Implémentation WebSocket pour Cotes en Temps Réel

## 📋 Architecture

```
Nouveau Pari → Signal Django → Broadcast WebSocket → Tous les clients connectés
```

## 🔧 Installation

### 1. Dépendances

```bash
pip install channels[daphne]
pip install channels-redis
pip install redis
```

### 2. Configuration Redis

**Sur le serveur :**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

## 📁 Structure des fichiers

```
merchex/
├── asgi.py                    # Configuration ASGI
├── routing.py                 # Routing WebSocket
├── listings/
│   ├── consumers.py          # WebSocket consumers
│   └── models.py             # Signal modifié
└── merchex/
    └── settings.py           # Configuration Channels
```

## 💾 Code à implémenter

### 1. `merchex/merchex/settings.py`

```python
# Ajouter à INSTALLED_APPS
INSTALLED_APPS = [
    'daphne',  # ← En premier !
    'channels',
    # ... autres apps
]

# Configuration Channels
ASGI_APPLICATION = 'merchex.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 2. `merchex/merchex/asgi.py`

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import listings.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'merchex.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                listings.routing.websocket_urlpatterns
            )
        )
    ),
})
```

### 3. `merchex/listings/routing.py` (NOUVEAU)

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/cotes/$', consumers.CotesConsumer.as_asgi()),
    re_path(r'ws/cotes/(?P<match_id>\w+)/$', consumers.CotesConsumer.as_asgi()),
]
```

### 4. `merchex/listings/consumers.py` (NOUVEAU)

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Match, Cote

class CotesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connexion au WebSocket"""
        self.match_id = self.scope['url_route']['kwargs'].get('match_id', 'all')

        if self.match_id == 'all':
            # S'abonner à tous les matchs
            self.room_group_name = 'cotes_all'
        else:
            # S'abonner à un match spécifique
            self.room_group_name = f'cotes_{self.match_id}'

        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Envoyer les cotes actuelles dès la connexion
        await self.send_current_cotes()

    async def disconnect(self, close_code):
        """Déconnexion du WebSocket"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Recevoir des messages du client (si nécessaire)"""
        pass

    async def send_current_cotes(self):
        """Envoyer les cotes actuelles au client"""
        if self.match_id != 'all':
            cotes_data = await self.get_cotes_for_match(self.match_id)
            await self.send(text_data=json.dumps({
                'type': 'cotes_update',
                'data': cotes_data
            }))

    @database_sync_to_async
    def get_cotes_for_match(self, match_id):
        """Récupérer les cotes d'un match"""
        try:
            cote = Cote.objects.get(match_id=match_id)
            return {
                'match_id': match_id,
                'cote1': float(cote.cote1),
                'cote2': float(cote.cote2),
                'coteN': float(cote.coteN),
                'last_updated': cote.last_updated.isoformat(),
                'paris_count': cote.paris_count_since_last_update
            }
        except Cote.DoesNotExist:
            return None

    async def cotes_update(self, event):
        """Recevoir une mise à jour de cotes et la transmettre au client"""
        await self.send(text_data=json.dumps({
            'type': 'cotes_update',
            'data': event['data']
        }))
```

### 5. Modifier `merchex/listings/models.py` - Signal

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@receiver(post_save, sender='listings.Pari')
def update_cotes_on_new_pari(sender, instance, created, **kwargs):
    """
    Signal déclenché à la création d'un nouveau pari.
    Incrémente le compteur et broadcast via WebSocket
    """
    if created:
        try:
            cote = Cote.objects.filter(match=instance.match).first()

            if cote:
                # Incrémenter le compteur
                cote.increment_paris_count()

                # Broadcaster la mise à jour via WebSocket
                channel_layer = get_channel_layer()

                cotes_data = {
                    'match_id': instance.match.id,
                    'cote1': float(cote.cote1),
                    'cote2': float(cote.cote2),
                    'coteN': float(cote.coteN),
                    'last_updated': cote.last_updated.isoformat(),
                    'paris_count': cote.paris_count_since_last_update
                }

                # Envoyer à tous les clients connectés au match
                async_to_sync(channel_layer.group_send)(
                    f'cotes_{instance.match.id}',
                    {
                        'type': 'cotes_update',
                        'data': cotes_data
                    }
                )

                # Envoyer aussi au groupe "all"
                async_to_sync(channel_layer.group_send)(
                    'cotes_all',
                    {
                        'type': 'cotes_update',
                        'data': cotes_data
                    }
                )

                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[WEBSOCKET] Cotes broadcasted pour match {instance.match.id}")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[WEBSOCKET] Erreur broadcast: {str(e)}")
```

## 🌐 Frontend - Client JavaScript

```javascript
// Connexion au WebSocket
const cotesSocket = new WebSocket(
    'wss://' + window.location.host + '/ws/cotes/'
);

// Écouter les mises à jour
cotesSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.type === 'cotes_update') {
        const cotes = data.data;

        // Mettre à jour l'interface
        updateCotesUI(cotes.match_id, {
            cote1: cotes.cote1,
            cote2: cotes.cote2,
            coteN: cotes.coteN
        });

        // Animation de changement
        highlightCoteChange(cotes.match_id);
    }
};

cotesSocket.onclose = function(e) {
    console.error('WebSocket fermé, reconnexion...');
    setTimeout(() => {
        // Reconnecter
    }, 1000);
};

// Fonction pour mettre à jour l'UI
function updateCotesUI(matchId, cotes) {
    document.querySelector(`#cote1-${matchId}`).textContent = cotes.cote1.toFixed(2);
    document.querySelector(`#cote2-${matchId}`).textContent = cotes.cote2.toFixed(2);
    document.querySelector(`#coteN-${matchId}`).textContent = cotes.coteN.toFixed(2);
}

// Animation de changement (effet flash)
function highlightCoteChange(matchId) {
    const elements = document.querySelectorAll(`[data-match-id="${matchId}"] .cote`);
    elements.forEach(el => {
        el.classList.add('cote-changed');
        setTimeout(() => el.classList.remove('cote-changed'), 1000);
    });
}
```

## 📊 Déploiement

### 1. Avec Daphne (ASGI Server)

**Fichier systemd : `/etc/systemd/system/daphne.service`**

```ini
[Unit]
Description=Daphne ASGI Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/BDD-test/merchex
ExecStart=/home/ubuntu/BDD-test/venv-test/bin/daphne -b 0.0.0.0 -p 8002 merchex.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**Démarrer :**
```bash
sudo systemctl daemon-reload
sudo systemctl start daphne
sudo systemctl enable daphne
```

### 2. Nginx Configuration

```nginx
# WebSocket proxy
location /ws/ {
    proxy_pass http://127.0.0.1:8002;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# HTTP normal (Gunicorn)
location / {
    proxy_pass http://127.0.0.1:8001;
}
```

## 🧪 Tests

```python
# Test de connexion WebSocket
from channels.testing import WebsocketCommunicator
from merchex.asgi import application
import pytest

@pytest.mark.asyncio
async def test_cotes_websocket():
    communicator = WebsocketCommunicator(
        application,
        "/ws/cotes/123/"
    )
    connected, _ = await communicator.connect()
    assert connected

    # Recevoir les cotes initiales
    response = await communicator.receive_json_from()
    assert response['type'] == 'cotes_update'

    await communicator.disconnect()
```

## 📈 Monitoring

```bash
# Vérifier que Redis fonctionne
redis-cli ping  # Devrait retourner PONG

# Voir les connexions WebSocket actives
redis-cli CLIENT LIST | grep channels

# Logs Daphne
journalctl -u daphne -f
```

## 🔒 Sécurité

### Authentication WebSocket

```python
# Dans consumers.py
async def connect(self):
    # Vérifier l'authentification
    if self.scope["user"].is_anonymous:
        await self.close()
        return

    # ... reste du code
```

## 🚀 Avantages de cette implémentation

1. ✅ **Vraiment temps réel** : les clients voient les cotes changer instantanément
2. ✅ **Scalable** : Redis gère la distribution entre serveurs
3. ✅ **Efficace** : pas de polling, connexion persistante
4. ✅ **UX excellente** : animations de changement, pas de refresh
5. ✅ **Bidirectionnel** : possibilité d'envoyer des messages au serveur

## ⚠️ Inconvénients

1. ⚠️ Plus complexe à déployer
2. ⚠️ Nécessite Redis (dépendance supplémentaire)
3. ⚠️ Nécessite ASGI server (Daphne/Uvicorn)
4. ⚠️ Plus de ressources serveur (connexions persistantes)

## 🎯 Recommandation

**OUI, implémente WebSocket si :**
- Tu veux une vraie expérience temps réel
- Tu as plusieurs utilisateurs simultanés
- Les cotes changent fréquemment
- Tu veux te démarquer avec une UX premium

**NON, reste avec le signal si :**
- Le projet est petit / prototype
- Infrastructure simple souhaitée
- Peu d'utilisateurs simultanés

---

**Pour ce projet de paris sportifs : Je recommande FORTEMENT WebSocket !** 🚀
