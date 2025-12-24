# 🚀 Guide complet de configuration WebSocket - TEST et PRODUCTION

## 📂 Structure des environnements

- **TEST** : `/home/ubuntu/BDD-test` → Port 8002 → `test.campus-league.com`
- **PRODUCTION** : `/home/user/BDD` → Port 8000 → `campus-league.com`

---

# 🧪 PARTIE 1 : Configuration SERVEUR TEST

## 1.1 Installation des dépendances WebSocket

```bash
# Aller dans le répertoire TEST
cd /home/ubuntu/BDD-test

# Activer le virtualenv
source venv-serveur/bin/activate

# Installer les packages WebSocket
pip install channels==4.0.0 daphne==4.0.0 channels-redis==4.1.0 redis==5.0.1

# Vérifier l'installation
python -c "import channels, daphne; print('✅ Packages installés')"
```

## 1.2 Copier les fichiers de configuration depuis PROD

```bash
# Copier les fichiers WebSocket depuis PROD
cp /home/user/BDD/merchex/merchex/asgi.py /home/ubuntu/BDD-test/merchex/merchex/asgi.py
cp /home/user/BDD/merchex/listings/routing.py /home/ubuntu/BDD-test/merchex/listings/routing.py
cp /home/user/BDD/merchex/listings/consumers.py /home/ubuntu/BDD-test/merchex/listings/consumers.py

# Vérifier la copie
ls -la /home/ubuntu/BDD-test/merchex/listings/ | grep -E "(routing|consumers)"
```

## 1.3 Vérifier la configuration Django

```bash
cd /home/ubuntu/BDD-test/merchex

# Vérifier settings.py
grep -A 5 "INSTALLED_APPS" merchex/settings.py | grep -E "(daphne|channels)"
grep -A 10 "ASGI_APPLICATION" merchex/settings.py
grep -A 10 "CHANNEL_LAYERS" merchex/settings.py
```

### Si ces sections n'existent pas, les ajouter :

```bash
# Éditer settings.py
nano merchex/settings.py
```

**Ajouter dans INSTALLED_APPS (en PREMIER) :**
```python
INSTALLED_APPS = [
    'daphne',  # ⬅️ EN PREMIER
    'channels',  # ⬅️ Après daphne
    'django.contrib.admin',
    # ... reste des apps
]
```

**Ajouter à la fin du fichier :**
```python
# Configuration ASGI pour WebSocket
ASGI_APPLICATION = 'merchex.asgi.application'

# Configuration Redis pour Channel Layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

## 1.4 Appliquer les migrations

```bash
cd /home/ubuntu/BDD-test/merchex
source ../venv-serveur/bin/activate

# Créer les nouvelles migrations (pour les champs realtime des cotes)
python manage.py makemigrations

# Appliquer toutes les migrations
python manage.py migrate
```

## 1.5 Créer le script de démarrage TEST

```bash
cat > /home/ubuntu/BDD-test/start-services-test.sh << 'EOF'
#!/bin/bash
# Script de démarrage des services TEST

set -e

echo "🚀 Démarrage des services TEST..."

# Variables
PROJECT_DIR="/home/ubuntu/BDD-test"
VENV_DIR="$PROJECT_DIR/venv-serveur"
DJANGO_DIR="$PROJECT_DIR/merchex"

# 1. Démarrer Redis
echo "[1/3] Démarrage Redis..."
redis-server --daemonize yes --port 6379
sleep 2
redis-cli ping && echo "✅ Redis démarré" || { echo "❌ Redis erreur"; exit 1; }

# 2. Migrations
echo "[2/3] Migrations..."
cd $DJANGO_DIR
source $VENV_DIR/bin/activate
python manage.py migrate --noinput

# 3. Démarrer Daphne
echo "[3/3] Démarrage Daphne..."
pkill -f "daphne.*8002" || true
sleep 1

nohup daphne -b 0.0.0.0 -p 8002 merchex.asgi:application \
    >> /tmp/daphne-test.log 2>&1 &

DAPHNE_PID=$!
sleep 3

if ps -p $DAPHNE_PID > /dev/null; then
    echo "✅ Daphne TEST démarré sur port 8002 (PID: $DAPHNE_PID)"
else
    echo "❌ Daphne erreur"
    tail -20 /tmp/daphne-test.log
    exit 1
fi

echo ""
echo "✅ Services TEST prêts !"
echo "  • Redis: port 6379"
echo "  • Daphne: port 8002"
EOF

chmod +x /home/ubuntu/BDD-test/start-services-test.sh
```

## 1.6 Créer le script d'arrêt TEST

```bash
cat > /home/ubuntu/BDD-test/stop-services-test.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt des services TEST..."
pkill -f "daphne.*8002" && echo "✅ Daphne arrêté" || echo "⚠️ Daphne non actif"
redis-cli shutdown && echo "✅ Redis arrêté" || echo "⚠️ Redis non actif"
echo "✅ Services TEST arrêtés"
EOF

chmod +x /home/ubuntu/BDD-test/stop-services-test.sh
```

## 1.7 Démarrer les services TEST

```bash
cd /home/ubuntu/BDD-test
./start-services-test.sh
```

## 1.8 Vérifier que TEST fonctionne

```bash
# Vérifier les processus
ps aux | grep -E "(daphne.*8002|redis)" | grep -v grep

# Tester l'API
curl http://localhost:8002/api/matches/filtered/

# Tester WebSocket
curl -i http://localhost:8002/ws/cotes/
```

---

# 🚀 PARTIE 2 : Configuration SERVEUR PRODUCTION

## 2.1 Vérifier les dépendances PROD

```bash
cd /home/user/BDD
source venv-websocket/bin/activate

# Vérifier que tout est installé
python -c "import channels, daphne, channels_redis; print('✅ Packages OK')"
```

## 2.2 Vérifier la configuration PROD

```bash
cd /home/user/BDD/merchex

# Vérifier que les fichiers existent
ls -la listings/routing.py listings/consumers.py merchex/asgi.py

# Vérifier settings.py
grep "daphne\|channels" merchex/settings.py
```

## 2.3 Appliquer les migrations PROD

```bash
cd /home/user/BDD/merchex
source ../venv-websocket/bin/activate

python manage.py makemigrations
python manage.py migrate
```

## 2.4 Créer le script de démarrage PROD

```bash
cat > /home/user/BDD/start-services-prod.sh << 'EOF'
#!/bin/bash
# Script de démarrage des services PRODUCTION

set -e

echo "🚀 Démarrage des services PRODUCTION..."

# Variables
PROJECT_DIR="/home/user/BDD"
VENV_DIR="$PROJECT_DIR/venv-websocket"
DJANGO_DIR="$PROJECT_DIR/merchex"

# 1. Redis
echo "[1/3] Démarrage Redis..."
redis-server --daemonize yes --port 6379
sleep 2
redis-cli ping && echo "✅ Redis démarré" || { echo "❌ Redis erreur"; exit 1; }

# 2. Migrations
echo "[2/3] Migrations..."
cd $DJANGO_DIR
source $VENV_DIR/bin/activate
python manage.py migrate --noinput

# 3. Daphne PRODUCTION
echo "[3/3] Démarrage Daphne PRODUCTION..."
pkill -f "daphne.*8000" || true
sleep 1

nohup daphne -b 0.0.0.0 -p 8000 merchex.asgi:application \
    >> /tmp/daphne-prod.log 2>&1 &

DAPHNE_PID=$!
sleep 3

if ps -p $DAPHNE_PID > /dev/null; then
    echo "✅ Daphne PRODUCTION démarré sur port 8000 (PID: $DAPHNE_PID)"
else
    echo "❌ Daphne erreur"
    tail -20 /tmp/daphne-prod.log
    exit 1
fi

echo ""
echo "✅ Services PRODUCTION prêts !"
echo "  • Redis: port 6379"
echo "  • Daphne: port 8000"
EOF

chmod +x /home/user/BDD/start-services-prod.sh
```

## 2.5 Créer le script d'arrêt PROD

```bash
cat > /home/user/BDD/stop-services-prod.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt des services PRODUCTION..."
pkill -f "daphne.*8000" && echo "✅ Daphne arrêté" || echo "⚠️ Daphne non actif"
redis-cli shutdown && echo "✅ Redis arrêté" || echo "⚠️ Redis non actif"
echo "✅ Services PRODUCTION arrêtés"
EOF

chmod +x /home/user/BDD/stop-services-prod.sh
```

## 2.6 Démarrer les services PROD

```bash
cd /home/user/BDD
./start-services-prod.sh
```

## 2.7 Vérifier que PROD fonctionne

```bash
# Vérifier les processus
ps aux | grep -E "(daphne.*8000|redis)" | grep -v grep

# Tester l'API
curl http://localhost:8000/api/matches/filtered/

# Tester WebSocket
curl -i http://localhost:8000/ws/cotes/
```

---

# 🔧 PARTIE 3 : Configuration Nginx

## 3.1 Éditer le fichier Nginx

```bash
sudo nano /etc/nginx/sites-available/campus-league.com
```

## 3.2 Configuration complète Nginx

Remplacez le contenu par :

```nginx
# ========================================
# SERVEUR TEST
# ========================================
server {
    listen 80;
    server_name test.campus-league.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name test.campus-league.com;

    ssl_certificate /etc/letsencrypt/live/campus-league.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/campus-league.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10M;

    # WebSocket TEST
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # Django TEST
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    location /static/ {
        alias /home/ubuntu/BDD-test/merchex/static/;
    }

    location /media/ {
        alias /home/ubuntu/BDD-test/merchex/media/;
    }
}

# ========================================
# SERVEUR PRODUCTION
# ========================================
server {
    listen 80;
    server_name campus-league.com www.campus-league.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    http2 on;
    server_name campus-league.com www.campus-league.com;

    ssl_certificate /etc/letsencrypt/live/campus-league.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/campus-league.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10M;

    # WebSocket PRODUCTION
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # Django PRODUCTION
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    location /static/ {
        alias /home/user/BDD/merchex/static/;
    }

    location /media/ {
        alias /home/user/BDD/merchex/media/;
    }
}
```

## 3.3 Tester et recharger Nginx

```bash
# Tester la syntaxe
sudo nginx -t

# Si OK, recharger
sudo systemctl reload nginx

# Vérifier le statut
sudo systemctl status nginx
```

---

# ✅ PARTIE 4 : Tests complets

## 4.1 Test serveur TEST

```bash
# Depuis le serveur
curl -I https://test.campus-league.com/api/matches/filtered/
curl -I https://test.campus-league.com/ws/cotes/

# Depuis le navigateur (Console F12)
const ws = new WebSocket('wss://test.campus-league.com/ws/cotes/');
ws.onopen = () => console.log('✅ TEST WebSocket OK');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## 4.2 Test serveur PRODUCTION

```bash
# Depuis le serveur
curl -I https://campus-league.com/api/matches/filtered/
curl -I https://campus-league.com/ws/cotes/

# Depuis le navigateur (Console F12)
const ws = new WebSocket('wss://campus-league.com/ws/cotes/');
ws.onopen = () => console.log('✅ PROD WebSocket OK');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

# 📊 PARTIE 5 : Gestion quotidienne

## Démarrer les services

```bash
# TEST
cd /home/ubuntu/BDD-test && ./start-services-test.sh

# PRODUCTION
cd /home/user/BDD && ./start-services-prod.sh
```

## Arrêter les services

```bash
# TEST
cd /home/ubuntu/BDD-test && ./stop-services-test.sh

# PRODUCTION
cd /home/user/BDD && ./stop-services-prod.sh
```

## Redémarrer après modification du code

```bash
# TEST
cd /home/ubuntu/BDD-test
./stop-services-test.sh
git pull  # si modifications
./start-services-test.sh

# PRODUCTION
cd /home/user/BDD
./stop-services-prod.sh
git pull  # si modifications
./start-services-prod.sh
```

## Voir les logs

```bash
# Logs Daphne TEST
tail -f /tmp/daphne-test.log

# Logs Daphne PRODUCTION
tail -f /tmp/daphne-prod.log

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Vérifier les processus

```bash
# Tout voir
ps aux | grep -E "(daphne|redis)" | grep -v grep

# Ports utilisés
netstat -tlnp | grep -E ":(6379|8000|8002)"
# OU
ss -tlnp | grep -E ":(6379|8000|8002)"
```

---

# 🎯 Récapitulatif final

| Élément | TEST | PRODUCTION |
|---------|------|------------|
| **Répertoire** | /home/ubuntu/BDD-test | /home/user/BDD |
| **Virtualenv** | venv-serveur | venv-websocket |
| **Port Daphne** | 8002 | 8000 |
| **Domaine** | test.campus-league.com | campus-league.com |
| **WebSocket URL** | wss://test.campus-league.com/ws/cotes/ | wss://campus-league.com/ws/cotes/ |
| **Script start** | ./start-services-test.sh | ./start-services-prod.sh |
| **Script stop** | ./stop-services-test.sh | ./stop-services-prod.sh |
| **Logs** | /tmp/daphne-test.log | /tmp/daphne-prod.log |

---

# 🚨 Dépannage

## Redis ne démarre pas

```bash
# Vérifier si déjà actif
ps aux | grep redis

# Tuer et redémarrer
pkill redis-server
redis-server --daemonize yes --port 6379
```

## Daphne ne démarre pas

```bash
# Voir les logs
tail -50 /tmp/daphne-test.log
tail -50 /tmp/daphne-prod.log

# Vérifier les imports Python
cd /home/ubuntu/BDD-test/merchex
source ../venv-serveur/bin/activate
python -c "import channels, daphne; print('OK')"
```

## WebSocket 404

```bash
# Vérifier les routes
cat /home/ubuntu/BDD-test/merchex/listings/routing.py
cat /home/user/BDD/merchex/listings/routing.py

# Les patterns doivent commencer par ^
```

## Nginx erreur

```bash
# Voir logs détaillés
sudo nginx -t
sudo tail -50 /var/log/nginx/error.log
```
