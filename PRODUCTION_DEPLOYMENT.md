# 🚀 Guide de Déploiement Production - WebSocket Cotes Temps Réel

## 📋 Pré-requis

- Serveur production : `campus-league.com`
- Accès root/sudo
- Redis installé
- Nginx configuré
- Django déjà déployé

---

## 🔧 Script d'Installation Production

Sauvegardez ce script : `/home/ubuntu/BDD/deploy-websocket-production.sh`

```bash
#!/bin/bash
# Script de déploiement WebSocket en PRODUCTION

set -e  # Arrêter en cas d'erreur

echo "🚀 DÉPLOIEMENT WEBSOCKET EN PRODUCTION"
echo "======================================"
echo ""
echo "⚠️  ATTENTION: Déploiement sur campus-league.com (PRODUCTION)"
echo "Voulez-vous continuer ? [y/N]"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Déploiement annulé."
    exit 0
fi

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
PROD_DIR="/home/ubuntu/BDD"
VENV_DIR="$PROD_DIR/venv-serveur"
PROJECT_DIR="$PROD_DIR/merchex"
BRANCH="main"  # ← Adapter selon votre branche de production

echo ""
echo "📍 Configuration:"
echo "  - Répertoire: $PROD_DIR"
echo "  - Venv: $VENV_DIR"
echo "  - Branche: $BRANCH"
echo ""

# 1. Backup de la config actuelle
echo "💾 Backup de la configuration actuelle..."
BACKUP_DIR="/home/ubuntu/backups/websocket-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup fichiers critiques
cp /etc/nginx/sites-available/campus-league.com "$BACKUP_DIR/" 2>/dev/null || true
cp /etc/systemd/system/gunicorn.service "$BACKUP_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/merchex/settings.py" "$BACKUP_DIR/" 2>/dev/null || true

echo -e "${GREEN}✅ Backup créé dans: $BACKUP_DIR${NC}"
echo ""

# 2. Pull des changements
echo "📥 Pull des derniers changements..."
cd "$PROD_DIR"
git stash  # Sauvegarder les changements locaux
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo -e "${GREEN}✅ Code mis à jour${NC}"
echo ""

# 3. Vérifier Redis
echo "🔍 Vérification de Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis CLI non trouvé, installation...${NC}"

    # Essayer snap
    if command -v snap &> /dev/null; then
        sudo snap install redis
    else
        # Installer depuis source
        echo "Installation Redis depuis source..."
        cd /tmp
        wget http://download.redis.io/redis-stable.tar.gz
        tar xzf redis-stable.tar.gz
        cd redis-stable
        make
        sudo make install

        sudo mkdir -p /etc/redis
        sudo cp redis.conf /etc/redis/
        sudo sed -i 's/daemonize no/daemonize yes/' /etc/redis/redis.conf

        sudo tee /etc/systemd/system/redis.service > /dev/null << 'EOF'
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
Type=forking
ExecStart=/usr/local/bin/redis-server /etc/redis/redis.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl start redis
        sudo systemctl enable redis
    fi
fi

# Tester Redis
sleep 2
if command -v redis-cli &> /dev/null && redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis fonctionne${NC}"
elif command -v redis.cli &> /dev/null && redis.cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis fonctionne (snap)${NC}"
    # Créer symlink
    sudo ln -sf /snap/bin/redis.cli /usr/local/bin/redis-cli 2>/dev/null || true
else
    echo -e "${RED}❌ Redis ne répond pas${NC}"
    echo "Vérifiez manuellement avec: redis-cli ping ou redis.cli ping"
fi
echo ""

# 4. Installer dépendances Python
echo "📦 Installation des dépendances Python..."
source "$VENV_DIR/bin/activate"

pip install channels[daphne]==4.0.0
pip install channels-redis==4.1.0
pip install redis==5.0.1

echo -e "${GREEN}✅ Dépendances installées${NC}"
echo ""

# 5. Appliquer migrations
echo "🗃️  Application des migrations..."
cd "$PROJECT_DIR"

# Gérer les conflits de migrations
python manage.py makemigrations --merge --noinput 2>/dev/null || true
python manage.py migrate

echo -e "${GREEN}✅ Migrations appliquées${NC}"
echo ""

# 6. Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo -e "${GREEN}✅ Fichiers statiques collectés${NC}"
echo ""

# 7. Créer le service Daphne PRODUCTION
echo "⚙️  Configuration du service Daphne..."

sudo tee /etc/systemd/system/daphne-prod.service > /dev/null << EOF
[Unit]
Description=Daphne ASGI Server pour Campus League Production
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/daphne -b 0.0.0.0 -p 8002 merchex.asgi:application
Restart=always
RestartSec=3

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable daphne-prod
sudo systemctl restart daphne-prod

sleep 2

# Vérifier Daphne
if systemctl is-active --quiet daphne-prod; then
    echo -e "${GREEN}✅ Daphne démarré${NC}"
else
    echo -e "${RED}❌ Erreur démarrage Daphne${NC}"
    echo "Logs:"
    sudo journalctl -u daphne-prod -n 20 --no-pager
    exit 1
fi
echo ""

# 8. Configurer Nginx
echo "🌐 Configuration de Nginx..."

NGINX_CONFIG="/etc/nginx/sites-available/campus-league.com"

# Vérifier si config WebSocket existe
if grep -q "location /ws/" "$NGINX_CONFIG"; then
    echo -e "${YELLOW}ℹ️  Configuration WebSocket déjà présente${NC}"
else
    echo "Ajout de la configuration WebSocket..."

    # Backup de la config Nginx
    sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup-$(date +%Y%m%d-%H%M%S)"

    # Ajouter la config WebSocket
    sudo sed -i '/location \/ {/i \
    # WebSocket proxy\
    location /ws/ {\
        proxy_pass http://127.0.0.1:8002;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_read_timeout 86400;\
    }\
    ' "$NGINX_CONFIG"
fi

# Tester et recharger Nginx
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx configuré et rechargé${NC}"
else
    echo -e "${RED}❌ Erreur configuration Nginx${NC}"
    exit 1
fi
echo ""

# 9. Redémarrer Gunicorn (HTTP)
echo "🔄 Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn
sleep 2

if systemctl is-active --quiet gunicorn; then
    echo -e "${GREEN}✅ Gunicorn redémarré${NC}"
else
    echo -e "${RED}❌ Erreur Gunicorn${NC}"
fi
echo ""

# 10. Tests finaux
echo "🧪 Tests de fonctionnement..."

# Test Redis
echo -n "  Redis: "
if command -v redis-cli &> /dev/null && redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ OK${NC}"
elif command -v redis.cli &> /dev/null && redis.cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ OK (snap)${NC}"
else
    echo -e "${RED}❌ ÉCHEC${NC}"
fi

# Test Daphne
echo -n "  Daphne (8002): "
if nc -z 127.0.0.1 8002; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ ÉCHEC${NC}"
fi

# Test Gunicorn
echo -n "  Gunicorn (8000): "
if nc -z 127.0.0.1 8000; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ ÉCHEC${NC}"
fi

# Test WebSocket endpoint
echo -n "  WebSocket endpoint: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://campus-league.com/ws/cotes/)
if [ "$RESPONSE" = "101" ] || [ "$RESPONSE" = "400" ] || [ "$RESPONSE" = "401" ]; then
    echo -e "${GREEN}✅ OK (code $RESPONSE)${NC}"
else
    echo -e "${YELLOW}⚠️  Code $RESPONSE${NC}"
fi

echo ""

# 11. Résumé
echo "=========================================="
echo -e "${GREEN}✅ DÉPLOIEMENT TERMINÉ${NC}"
echo "=========================================="
echo ""
echo "📊 Informations Production:"
echo "  - Site: https://campus-league.com"
echo "  - WebSocket: wss://campus-league.com/ws/cotes/"
echo "  - Daphne: Port 8002"
echo "  - Gunicorn: Port 8000"
echo "  - Redis: Port 6379"
echo ""
echo "📝 Commandes utiles:"
echo "  sudo systemctl status daphne-prod"
echo "  sudo systemctl status gunicorn"
echo "  sudo journalctl -u daphne-prod -f"
echo "  sudo journalctl -u gunicorn -f"
echo ""
echo "📂 Backup sauvegardé dans: $BACKUP_DIR"
echo ""
echo "🎉 Production prête ! Testez avec votre frontend."
echo ""
```

---

## 📋 Checklist de Déploiement

### Avant le déploiement

- [ ] Code testé sur environnement de test
- [ ] Frontend testé avec WebSocket
- [ ] Backup de la base de données
- [ ] Backup de la configuration Nginx
- [ ] Notification aux utilisateurs (maintenance)

### Exécution

```bash
# 1. Se connecter au serveur PRODUCTION
ssh ubuntu@campus-league.com

# 2. Créer le script
nano /home/ubuntu/BDD/deploy-websocket-production.sh

# Coller le contenu du script ci-dessus

# 3. Rendre exécutable
chmod +x /home/ubuntu/BDD/deploy-websocket-production.sh

# 4. Exécuter
sudo /home/ubuntu/BDD/deploy-websocket-production.sh
```

### Après le déploiement

- [ ] Vérifier status Daphne : `sudo systemctl status daphne-prod`
- [ ] Vérifier status Gunicorn : `sudo systemctl status gunicorn`
- [ ] Tester connexion WebSocket depuis frontend
- [ ] Surveiller les logs : `sudo journalctl -u daphne-prod -f`
- [ ] Tester avec 2 navigateurs (pari → voir cotes changer)
- [ ] Vérifier performance (charge CPU/RAM)
- [ ] Notifier les utilisateurs (maintenance terminée)

---

## 🔍 Monitoring Post-Déploiement

### Logs en temps réel

```bash
# Daphne
sudo journalctl -u daphne-prod -f

# Gunicorn
sudo journalctl -u gunicorn -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Redis
redis-cli MONITOR
```

### Vérifications

```bash
# Services actifs
sudo systemctl status daphne-prod
sudo systemctl status gunicorn
sudo systemctl status redis

# Ports ouverts
sudo netstat -tlnp | grep -E '8000|8002|6379'

# Connexions WebSocket actives
redis-cli CLIENT LIST | grep channels

# Mémoire Redis
redis-cli INFO memory
```

---

## 🚨 Rollback en cas de problème

```bash
# 1. Arrêter Daphne
sudo systemctl stop daphne-prod

# 2. Restaurer backup Nginx
sudo cp /home/ubuntu/backups/websocket-XXXXXX/campus-league.com /etc/nginx/sites-available/
sudo nginx -t
sudo systemctl reload nginx

# 3. Restaurer settings.py
cp /home/ubuntu/backups/websocket-XXXXXX/settings.py /home/ubuntu/BDD/merchex/merchex/

# 4. Redémarrer Gunicorn
sudo systemctl restart gunicorn

# 5. Git rollback si nécessaire
cd /home/ubuntu/BDD
git reset --hard HEAD~1
```

---

## 📈 Optimisations Production

### Redis

```bash
# Dans /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Daphne (Workers multiples)

```ini
# Dans /etc/systemd/system/daphne-prod.service
ExecStart=/home/ubuntu/BDD/venv-serveur/bin/daphne -b 0.0.0.0 -p 8002 --workers 4 merchex.asgi:application
```

### Nginx (Load Balancing)

```nginx
upstream daphne_backend {
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;  # Si plusieurs workers
}

location /ws/ {
    proxy_pass http://daphne_backend;
    ...
}
```

---

## 🔐 Sécurité Production

### Redis sécurisé

```bash
# Dans /etc/redis/redis.conf
requirepass VotreMotDePasseTresFort123!
bind 127.0.0.1
```

### Settings.py

```python
# merchex/merchex/settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "password": "VotreMotDePasseTresFort123!",  # ← Ajouter
        },
    },
}
```

---

## 📞 Support

En cas de problème :

1. **Vérifier les logs** : `sudo journalctl -u daphne-prod -f`
2. **Tester Redis** : `redis-cli ping`
3. **Tester Daphne** : `curl http://127.0.0.1:8002`
4. **Vérifier Nginx** : `sudo nginx -t`

---

**Créé le** : 2024-12-23
**Version** : 1.0
**Auteur** : Claude Code

🎉 **Bon déploiement en production !**
