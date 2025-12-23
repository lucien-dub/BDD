#!/bin/bash
# Script d'installation complète du système WebSocket

echo "🚀 INSTALLATION WEBSOCKET POUR COTES EN TEMPS RÉEL"
echo "===================================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier qu'on est sur le serveur test
echo "📍 Vérification de l'environnement..."
if [ ! -d "/home/ubuntu/BDD-test" ]; then
    echo -e "${RED}❌ Erreur: Ce script doit être exécuté sur le serveur de test${NC}"
    exit 1
fi

cd /home/ubuntu/BDD-test
echo -e "${GREEN}✅ Répertoire correct${NC}"
echo ""

# 2. Installer Redis
echo "📦 Installation de Redis..."
if ! command -v redis-server &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y redis-server
    echo -e "${GREEN}✅ Redis installé${NC}"
else
    echo -e "${YELLOW}ℹ️  Redis déjà installé${NC}"
fi

# Configurer Redis pour démarrer automatiquement
sudo systemctl start redis
sudo systemctl enable redis

# Vérifier que Redis fonctionne
if redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis fonctionne correctement${NC}"
else
    echo -e "${RED}❌ Erreur: Redis ne répond pas${NC}"
    exit 1
fi
echo ""

# 3. Installer les dépendances Python
echo "📦 Installation des dépendances Python WebSocket..."
cd /home/ubuntu/BDD-test
source venv-test/bin/activate

pip install channels[daphne]==4.0.0
pip install channels-redis==4.1.0
pip install redis==5.0.1

echo -e "${GREEN}✅ Dépendances Python installées${NC}"
echo ""

# 4. Appliquer les migrations
echo "🗃️  Application des migrations Django..."
cd merchex
python manage.py migrate listings

echo -e "${GREEN}✅ Migrations appliquées${NC}"
echo ""

# 5. Créer le service Daphne
echo "⚙️  Configuration du service Daphne..."
sudo bash /home/ubuntu/BDD-test/daphne-service.sh

sudo systemctl daemon-reload
sudo systemctl start daphne-test
sudo systemctl enable daphne-test

sleep 2

# Vérifier que Daphne fonctionne
if systemctl is-active --quiet daphne-test; then
    echo -e "${GREEN}✅ Daphne démarré et actif${NC}"
else
    echo -e "${RED}❌ Erreur: Daphne ne démarre pas${NC}"
    echo "Logs:"
    sudo journalctl -u daphne-test -n 20 --no-pager
    exit 1
fi
echo ""

# 6. Configurer Nginx pour WebSocket
echo "🌐 Configuration de Nginx pour WebSocket..."

NGINX_CONFIG="/etc/nginx/sites-available/test.campus-league.com"

# Vérifier si la config WebSocket existe déjà
if grep -q "location /ws/" $NGINX_CONFIG; then
    echo -e "${YELLOW}ℹ️  Configuration WebSocket déjà présente dans Nginx${NC}"
else
    echo "Ajout de la configuration WebSocket..."

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
    ' $NGINX_CONFIG

    # Recharger Nginx
    sudo nginx -t
    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        echo -e "${GREEN}✅ Nginx configuré et rechargé${NC}"
    else
        echo -e "${RED}❌ Erreur de configuration Nginx${NC}"
        exit 1
    fi
fi
echo ""

# 7. Tests de fonctionnement
echo "🧪 Tests de fonctionnement..."

# Test Redis
echo -n "Test Redis: "
if redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ ÉCHEC${NC}"
fi

# Test Daphne
echo -n "Test Daphne (port 8002): "
if nc -z 127.0.0.1 8002; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ ÉCHEC${NC}"
fi

# Test WebSocket endpoint
echo -n "Test WebSocket endpoint: "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/ws/cotes/)
if [ "$RESPONSE" = "101" ] || [ "$RESPONSE" = "400" ]; then
    echo -e "${GREEN}✅ OK (code $RESPONSE)${NC}"
else
    echo -e "${YELLOW}⚠️  Code $RESPONSE (peut nécessiter authentification)${NC}"
fi

echo ""

# 8. Afficher les informations finales
echo "===================================================="
echo -e "${GREEN}✅ INSTALLATION TERMINÉE${NC}"
echo "===================================================="
echo ""
echo "📊 Informations:"
echo "  - Redis: Port 6379"
echo "  - Daphne: Port 8002"
echo "  - WebSocket URL: wss://test.campus-league.com/ws/cotes/"
echo ""
echo "📝 Commandes utiles:"
echo "  Logs Daphne:  sudo journalctl -u daphne-test -f"
echo "  Logs Redis:   sudo journalctl -u redis -f"
echo "  Restart Daphne: sudo systemctl restart daphne-test"
echo "  Test Redis:   redis-cli ping"
echo "  Monitoring:   redis-cli MONITOR"
echo ""
echo "📖 Documentation frontend: FRONTEND_WEBSOCKET_CHECKLIST.md"
echo ""
echo "🎉 Prêt à tester ! Ouvrez votre frontend et regardez les cotes changer en temps réel !"
echo ""
