#!/bin/bash

# Script de démarrage des services pour serveur TEST
# Usage: ./start-services-test.sh

set -e

echo "🚀 Démarrage des services pour serveur TEST..."

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/home/user/BDD"
VENV_DIR="$PROJECT_DIR/venv-websocket"
DJANGO_DIR="$PROJECT_DIR/merchex"

# 1. Démarrer Redis
echo -e "${YELLOW}[1/4] Démarrage de Redis...${NC}"
redis-server --daemonize yes --port 6379
sleep 2
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis démarré sur port 6379${NC}"
else
    echo -e "${RED}❌ Erreur: Redis n'a pas démarré${NC}"
    exit 1
fi

# 2. Activer virtualenv et appliquer migrations
echo -e "${YELLOW}[2/4] Application des migrations Django...${NC}"
cd $DJANGO_DIR
source $VENV_DIR/bin/activate

python manage.py migrate --noinput
echo -e "${GREEN}✅ Migrations appliquées${NC}"

# 3. Collecter les fichiers statiques (optionnel)
echo -e "${YELLOW}[3/4] Collecte des fichiers statiques...${NC}"
python manage.py collectstatic --noinput --clear 2>/dev/null || echo "Skipped"

# 4. Démarrer Daphne (WebSocket + HTTP)
echo -e "${YELLOW}[4/4] Démarrage de Daphne...${NC}"

# Tuer les anciens processus Daphne
pkill -f daphne || true
sleep 1

# Démarrer Daphne en arrière-plan
nohup daphne -b 0.0.0.0 -p 8002 merchex.asgi:application \
    >> /tmp/daphne-test.log 2>&1 &

DAPHNE_PID=$!
sleep 3

# Vérifier que Daphne tourne
if ps -p $DAPHNE_PID > /dev/null; then
    echo -e "${GREEN}✅ Daphne démarré sur port 8002 (PID: $DAPHNE_PID)${NC}"
else
    echo -e "${RED}❌ Erreur: Daphne n'a pas démarré${NC}"
    echo "Logs:"
    tail -20 /tmp/daphne-test.log
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ TOUS LES SERVICES SONT DÉMARRÉS               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📊 Statut des services:"
echo "  • Redis:    $(redis-cli ping)"
echo "  • Daphne:   http://localhost:8002 (PID: $DAPHNE_PID)"
echo ""
echo "📝 Commandes utiles:"
echo "  • Voir logs Daphne:  tail -f /tmp/daphne-test.log"
echo "  • Tester WebSocket:  curl http://localhost:8002/ws/cotes/"
echo "  • Arrêter services:  ./stop-services-test.sh"
echo ""
