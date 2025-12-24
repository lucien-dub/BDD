# 🌐 Configuration Nginx - TEST vs PRODUCTION

## 📊 Différences entre les environnements

| Aspect | TEST | PRODUCTION |
|--------|------|------------|
| **Domaine** | test.campus-league.com | campus-league.com |
| **Port Daphne** | 8002 | 8000 (ou autre) |
| **Conteneur/Serveur** | Container BDD-test | Serveur principal |
| **URL WebSocket** | wss://test.campus-league.com/ws/cotes/ | wss://campus-league.com/ws/cotes/ |
| **Certificat SSL** | Partagé avec production | /etc/letsencrypt/live/campus-league.com/ |
| **Logs** | /var/log/nginx/test.campus-league.*.log | /var/log/nginx/campus-league.*.log |

---

## 🧪 SERVEUR TEST (test.campus-league.com)

### Configuration actuelle

```nginx
server {
    listen 443 ssl http2;
    server_name test.campus-league.com;

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;  # Daphne TEST
        # ... headers WebSocket ...
    }

    # Routes Django
    location / {
        proxy_pass http://127.0.0.1:8002;  # Daphne TEST
    }
}
```

### Services dans le conteneur BDD-test
- **Redis** : port 6379
- **Daphne** : port 8002
- **Script de démarrage** : `./start-services-test.sh`

### Démarrage des services TEST
```bash
# Dans le conteneur BDD-test
cd /home/user/BDD
./start-services-test.sh
```

---

## 🚀 SERVEUR PRODUCTION (campus-league.com)

### Configuration à appliquer

```nginx
server {
    listen 443 ssl http2;
    server_name campus-league.com www.campus-league.com;

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;  # Daphne PRODUCTION
        # ... headers WebSocket ...
    }

    # Routes Django
    location / {
        proxy_pass http://127.0.0.1:8000;  # Daphne PRODUCTION
    }
}
```

### Services sur le serveur de production

Vous devrez installer les mêmes services que sur TEST :

1. **Redis**
```bash
# Option 1 : Via apt
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Option 2 : Via snap
sudo snap install redis
```

2. **Daphne** (avec venv production)
```bash
cd /chemin/vers/projet/production
source venv/bin/activate
pip install channels daphne channels-redis redis

# Démarrer Daphne (en production, utilisez systemd)
daphne -b 0.0.0.0 -p 8000 merchex.asgi:application
```

3. **Service systemd pour Daphne** (recommandé)
```bash
sudo nano /etc/systemd/system/daphne-prod.service
```

Contenu :
```ini
[Unit]
Description=Daphne ASGI Server (Production)
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/chemin/vers/projet/production/merchex
Environment="PATH=/chemin/vers/projet/production/venv/bin"
ExecStart=/chemin/vers/projet/production/venv/bin/daphne -b 127.0.0.1 -p 8000 merchex.asgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Puis :
```bash
sudo systemctl daemon-reload
sudo systemctl start daphne-prod
sudo systemctl enable daphne-prod
sudo systemctl status daphne-prod
```

---

## 📝 Fichiers Nginx à éditer

### Pour TEST
```bash
sudo nano /etc/nginx/sites-available/campus-league.com
```

Cherchez le bloc `server` avec `server_name test.campus-league.com` et ajoutez la section WebSocket.

### Pour PRODUCTION
```bash
sudo nano /etc/nginx/sites-available/campus-league.com
```

Cherchez le bloc `server` avec `server_name campus-league.com` et ajoutez la section WebSocket.

**OU** si vous avez des fichiers séparés :
```bash
sudo nano /etc/nginx/sites-available/campus-league.com      # Production
sudo nano /etc/nginx/sites-available/test.campus-league.com # Test
```

---

## 🔍 Vérifier la configuration actuelle

```bash
# Voir tous les fichiers de config
ls -la /etc/nginx/sites-available/
ls -la /etc/nginx/sites-enabled/

# Afficher la config complète compilée
sudo nginx -T | grep -A 20 "server_name campus-league.com"
sudo nginx -T | grep -A 20 "server_name test.campus-league.com"
```

---

## ⚙️ Ports utilisés

### Actuellement (AVANT WebSocket)
- **Production** : Port 8001 (Gunicorn ?)
- **Test** : Port 8001 (Gunicorn ?)

### Après migration WebSocket
- **Production** : Port 8000 → Daphne (HTTP + WebSocket)
- **Test** : Port 8002 → Daphne (HTTP + WebSocket)

⚠️ **Important** : Daphne remplace Gunicorn pour gérer à la fois HTTP classique et WebSocket.

---

## 📋 Checklist de migration

### TEST (déjà fait ✅)
- [x] Redis installé et démarré
- [x] Daphne installé (venv-websocket)
- [x] Migrations appliquées
- [x] Services démarrés (port 8002)
- [ ] Nginx configuré (à faire)

### PRODUCTION (à faire)
- [ ] Redis installé
- [ ] Daphne installé dans venv production
- [ ] Migrations appliquées
- [ ] Service systemd créé pour Daphne
- [ ] Nginx configuré
- [ ] Tests effectués

---

## 🧪 Tests après configuration

### TEST
```bash
# WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://test.campus-league.com/ws/cotes/

# API REST
curl https://test.campus-league.com/api/matches/filtered/
```

### PRODUCTION
```bash
# WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://campus-league.com/ws/cotes/

# API REST
curl https://campus-league.com/api/matches/filtered/
```

---

## 🎯 URLs finales

### TEST
- WebSocket : `wss://test.campus-league.com/ws/cotes/`
- API : `https://test.campus-league.com/api/`
- Admin : `https://test.campus-league.com/admin/`

### PRODUCTION
- WebSocket : `wss://campus-league.com/ws/cotes/`
- API : `https://campus-league.com/api/`
- Admin : `https://campus-league.com/admin/`

---

## 🔄 Workflow recommandé

1. **Tester d'abord sur TEST** ✅
2. **Valider le fonctionnement WebSocket sur TEST**
3. **Une fois validé, déployer sur PRODUCTION**
4. **Monitorer les logs de production**

```bash
# Logs production
sudo tail -f /var/log/nginx/campus-league.error.log
sudo journalctl -u daphne-prod -f
```
