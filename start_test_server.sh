#!/bin/bash

echo "🚀 DÉMARRAGE DU SERVEUR TEST"
echo "============================"
echo ""

# 1. Tuer tous les processus Gunicorn existants
echo "1️⃣ Arrêt des processus Gunicorn existants..."
pkill -f gunicorn
sleep 2
echo "✅ Processus arrêtés"
echo ""

# 2. Vérifier la branche Git
echo "2️⃣ Vérification de la branche Git..."
cd /home/ubuntu/BDD-test
CURRENT_BRANCH=$(git branch --show-current)
echo "Branche actuelle: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "claude/add-all-users-bets-endpoint-01UPVCBx4Kmz3Hip1vfxLrL9" ]; then
    echo "⚠️  Pas sur la bonne branche. Checkout..."
    git checkout claude/add-all-users-bets-endpoint-01UPVCBx4Kmz3Hip1vfxLrL9
fi
echo "✅ Branche correcte"
echo ""

# 3. Vérifier ALLOWED_HOSTS
echo "3️⃣ Vérification ALLOWED_HOSTS..."
if grep -q "test.campus-league.com" merchex/merchex/settings.py; then
    echo "✅ test.campus-league.com déjà dans ALLOWED_HOSTS"
else
    echo "⚠️  Ajout de test.campus-league.com dans ALLOWED_HOSTS..."
    sed -i "s/ALLOWED_HOSTS = \[/ALLOWED_HOSTS = ['test.campus-league.com',/" merchex/merchex/settings.py
    echo "✅ ALLOWED_HOSTS mis à jour"
fi
echo ""

# 4. Choisir le bon environnement virtuel
echo "4️⃣ Activation de l'environnement virtuel..."
if [ -d "venv-test" ] && [ -f "venv-test/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-test"
    echo "Utilisation de venv-test"
elif [ -d "venv-myapp" ] && [ -f "venv-myapp/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-myapp"
    echo "Utilisation de venv-myapp"
elif [ -d "venv-bdd" ] && [ -f "venv-bdd/bin/gunicorn" ]; then
    VENV_PATH="/home/ubuntu/BDD-test/venv-bdd"
    echo "Utilisation de venv-bdd"
else
    echo "❌ Aucun environnement virtuel avec gunicorn trouvé"
    echo "Installation de gunicorn dans venv-myapp..."
    source /home/ubuntu/BDD-test/venv-myapp/bin/activate
    pip install gunicorn
    VENV_PATH="/home/ubuntu/BDD-test/venv-myapp"
fi
echo "✅ Environnement: $VENV_PATH"
echo ""

# 5. Démarrer Gunicorn
echo "5️⃣ Démarrage de Gunicorn sur port 8001..."
cd /home/ubuntu/BDD-test/merchex
nohup $VENV_PATH/bin/gunicorn merchex.wsgi:application --bind 127.0.0.1:8001 --workers 3 > /tmp/gunicorn-test.log 2>&1 &
sleep 3
echo "✅ Gunicorn démarré"
echo ""

# 6. Vérifier que Gunicorn tourne
echo "6️⃣ Vérification des processus..."
ps aux | grep gunicorn | grep -v grep | grep 8001
if [ $? -eq 0 ]; then
    echo "✅ Gunicorn tourne sur port 8001"
else
    echo "❌ Erreur: Gunicorn ne tourne pas"
    echo "Logs:"
    tail -20 /tmp/gunicorn-test.log
    exit 1
fi
echo ""

# 7. Vérifier que le code est bien chargé depuis BDD-test
echo "7️⃣ Vérification du répertoire de chargement..."
ps aux | grep gunicorn | grep -v grep | head -1
if ps aux | grep gunicorn | grep -v grep | grep -q "BDD-test"; then
    echo "✅ Gunicorn charge le code depuis BDD-test"
elif ps aux | grep gunicorn | grep -v grep | grep -q "BDD/"; then
    echo "❌ ERREUR: Gunicorn charge le code depuis BDD (serveur normal)"
    echo "Le problème vient de l'environnement virtuel partagé"
    exit 1
else
    echo "⚠️  Impossible de déterminer le répertoire de chargement"
fi
echo ""

# 8. Tester l'endpoint directement
echo "8️⃣ Test de l'endpoint /api/academies/available/..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/api/academies/available/)
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ]; then
    echo "✅ Endpoint répond (HTTP $RESPONSE)"
    curl -s http://127.0.0.1:8001/api/academies/available/ | head -5
elif [ "$RESPONSE" = "404" ]; then
    echo "❌ ERREUR: Endpoint retourne 404"
    echo "Les endpoints ne sont pas présents dans le code chargé"
    exit 1
else
    echo "⚠️  Réponse HTTP: $RESPONSE"
fi
echo ""

# 9. Test via HTTPS
echo "9️⃣ Test via HTTPS test.campus-league.com..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/api/academies/available/)
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "401" ]; then
    echo "✅ HTTPS fonctionne (HTTP $RESPONSE)"
elif [ "$RESPONSE" = "502" ]; then
    echo "❌ Erreur 502 Bad Gateway - Nginx ne peut pas se connecter à Gunicorn"
elif [ "$RESPONSE" = "404" ]; then
    echo "❌ Erreur 404 - Endpoint non trouvé"
else
    echo "⚠️  Réponse HTTP: $RESPONSE"
fi
echo ""

echo "============================"
echo "✅ SERVEUR TEST DÉMARRÉ"
echo "============================"
echo ""
echo "📊 Statut:"
echo "  - Port: 8001"
echo "  - Workers: 3"
echo "  - Logs: /tmp/gunicorn-test.log"
echo "  - URL: https://test.campus-league.com"
echo ""
echo "📝 Pour voir les logs:"
echo "  tail -f /tmp/gunicorn-test.log"
echo ""
echo "🛑 Pour arrêter:"
echo "  pkill -f 'gunicorn.*8001'"
echo ""
