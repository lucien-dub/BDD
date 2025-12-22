#!/bin/bash

echo "🚀 DÉPLOIEMENT DES CHANGEMENTS SUR LE SERVEUR TEST"
echo "=================================================="
echo ""

# 1. Aller dans le répertoire du serveur test
echo "📁 Navigation vers /home/ubuntu/BDD-test..."
cd /home/ubuntu/BDD-test || exit 1
echo "✅ Répertoire trouvé"
echo ""

# 2. Vérifier la branche actuelle
echo "🔍 Vérification de la branche Git..."
CURRENT_BRANCH=$(git branch --show-current)
echo "Branche actuelle: $CURRENT_BRANCH"
echo ""

# 3. Stash les changements locaux s'il y en a
echo "💾 Sauvegarde des changements locaux éventuels..."
git stash
echo ""

# 4. Pull les derniers changements
echo "📥 Pull des derniers changements..."
git pull origin claude/add-all-users-bets-endpoint-01UPVCBx4Kmz3Hip1vfxLrL9
if [ $? -eq 0 ]; then
    echo "✅ Pull réussi"
else
    echo "❌ Erreur lors du pull"
    exit 1
fi
echo ""

# 5. Nettoyer le cache Python
echo "🧹 Nettoyage du cache Python..."
sudo find merchex -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo find merchex -name "*.pyc" -delete 2>/dev/null
echo "✅ Cache nettoyé"
echo ""

# 6. Redémarrer Gunicorn
echo "🔄 Redémarrage de Gunicorn..."
echo "  - Arrêt des processus existants..."
sudo pkill -9 -f "gunicorn.*8001"
sleep 2

echo "  - Démarrage du nouveau processus..."
cd /home/ubuntu/BDD-test/merchex

# Déterminer le bon environnement virtuel
if [ -d "/home/ubuntu/BDD-test/venv-test" ] && [ -f "/home/ubuntu/BDD-test/venv-test/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-test"
elif [ -d "/home/ubuntu/BDD-test/venv-myapp" ] && [ -f "/home/ubuntu/BDD-test/venv-myapp/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-myapp"
elif [ -d "/home/ubuntu/BDD-test/venv-bdd" ] && [ -f "/home/ubuntu/BDD-test/venv-bdd/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-bdd"
else
    echo "❌ Aucun environnement virtuel trouvé"
    exit 1
fi

echo "  - Environnement: $VENV_PATH"
nohup $VENV_PATH/bin/gunicorn merchex.wsgi:application --bind 127.0.0.1:8001 --workers 3 > /tmp/gunicorn-test.log 2>&1 &
sleep 3
echo "✅ Gunicorn redémarré"
echo ""

# 7. Vérifier que Gunicorn fonctionne
echo "✔️  Vérification du processus Gunicorn..."
if ps aux | grep gunicorn | grep -v grep | grep 8001 > /dev/null; then
    echo "✅ Gunicorn est en cours d'exécution sur le port 8001"
    ps aux | grep gunicorn | grep -v grep | grep 8001 | head -1
else
    echo "❌ Gunicorn ne semble pas tourner"
    echo "Logs:"
    tail -20 /tmp/gunicorn-test.log
    exit 1
fi
echo ""

# 8. Tester les nouveaux endpoints
echo "🧪 Test des endpoints corrigés..."
echo ""

echo "Test 1: /api/results/filtered/ (matchs terminés)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/api/results/filtered/?page=1&page_size=10)
echo "  Status: $RESPONSE"
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ]; then
    echo "  ✅ Endpoint répond correctement"
else
    echo "  ⚠️  Réponse inattendue"
fi
echo ""

echo "Test 2: /api/matches/filtered/ (matchs à venir)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/api/matches/filtered/?page=1&page_size=15)
echo "  Status: $RESPONSE"
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ]; then
    echo "  ✅ Endpoint répond correctement"
else
    echo "  ⚠️  Réponse inattendue"
fi
echo ""

echo "Test 3: /api/available-academies/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/api/available-academies/)
echo "  Status: $RESPONSE"
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ]; then
    echo "  ✅ Endpoint répond correctement"
else
    echo "  ⚠️  Réponse inattendue"
fi
echo ""

echo "=================================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=================================================="
echo ""
echo "📊 Informations:"
echo "  - Port: 8001"
echo "  - URL: https://test.campus-league.com"
echo "  - Logs: /tmp/gunicorn-test.log"
echo ""
echo "📝 Pour voir les logs en temps réel:"
echo "  tail -f /tmp/gunicorn-test.log"
echo ""
