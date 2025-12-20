#!/bin/bash

echo "🔍 DIAGNOSTIC DU SERVEUR TEST"
echo "================================"
echo ""

# 1. Vérifier si gunicorn tourne
echo "📊 1. Vérification de Gunicorn..."
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn est en cours d'exécution"
    ps aux | grep gunicorn | grep -v grep
else
    echo "❌ Gunicorn n'est PAS en cours d'exécution"
fi
echo ""

# 2. Vérifier les dernières erreurs Django
echo "📋 2. Dernières erreurs Django (10 dernières lignes):"
if [ -f "/home/ubuntu/BDD/merchex/logs/django.log" ]; then
    tail -10 /home/ubuntu/BDD/merchex/logs/django.log
else
    echo "⚠️  Fichier log Django introuvable"
fi
echo ""

# 3. Vérifier nginx
echo "📊 3. Vérification de Nginx..."
sudo systemctl status nginx --no-pager | head -10
echo ""

# 4. Vérifier le statut git
echo "📂 4. Statut Git du projet:"
cd /home/ubuntu/BDD || exit
git log --oneline -3
git status
echo ""

echo "================================"
echo "🔧 REDÉMARRAGE DES SERVICES"
echo "================================"
echo ""

# 5. Arrêter gunicorn
echo "⏹️  Arrêt de Gunicorn..."
pkill -f gunicorn
sleep 2

# 6. Démarrer gunicorn
echo "🚀 Démarrage de Gunicorn..."
cd /home/ubuntu/BDD/merchex || exit
source /home/ubuntu/BDD/venv-bdd/bin/activate
gunicorn merchex.wsgi:application -c gunicorn_config.py --daemon
sleep 3

# 7. Vérifier si gunicorn a bien démarré
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn redémarré avec succès"
else
    echo "❌ Erreur: Gunicorn n'a pas démarré"
    echo "Essai de démarrage manuel..."
    gunicorn merchex.wsgi:application --bind 127.0.0.1:8000 --daemon
fi

# 8. Redémarrer nginx
echo "🔄 Redémarrage de Nginx..."
sudo systemctl restart nginx
sleep 2

# 9. Test final
echo ""
echo "================================"
echo "🧪 TESTS FINAUX"
echo "================================"
echo ""

echo "🔍 Test de l'endpoint /api/academies/available/..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/api/academies/available/ || echo "❌ Échec de connexion"

echo ""
echo "✅ Script terminé!"
echo "Vérifiez l'application maintenant."
