#!/bin/bash

echo "🔧 CORRECTION ALLOWED_HOSTS pour le serveur test"
echo "================================================"
echo ""

# Vérifier qu'on est sur le serveur test
if [ ! -d "/home/ubuntu/BDD-test" ]; then
    echo "❌ Ce script doit être exécuté sur le serveur (pas en local)"
    echo "Utilisez: ssh ubuntu@... puis exécutez ce script"
    exit 1
fi

SETTINGS_FILE="/home/ubuntu/BDD-test/merchex/merchex/settings.py"

# Vérifier que le fichier existe
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "❌ Fichier settings.py introuvable: $SETTINGS_FILE"
    exit 1
fi

echo "📄 Fichier settings.py trouvé: $SETTINGS_FILE"
echo ""

# Vérifier si test.campus-league.com est déjà présent
if grep -q "test.campus-league.com" "$SETTINGS_FILE"; then
    echo "✅ 'test.campus-league.com' est déjà dans ALLOWED_HOSTS"
    echo ""
    echo "Configuration actuelle:"
    grep "ALLOWED_HOSTS" "$SETTINGS_FILE"
    echo ""
    echo "⚠️  Malgré cela, vous avez l'erreur. Vérifiez que:"
    echo "  1. Le fichier a bien été sauvegardé"
    echo "  2. Gunicorn a été redémarré après la modification"
    echo ""
    echo "Pour redémarrer Gunicorn:"
    echo "  sudo pkill -9 -f 'gunicorn.*8001'"
    echo "  cd /home/ubuntu/BDD-test/merchex"
    echo "  nohup /home/ubuntu/BDD-test/venv-test/bin/gunicorn merchex.wsgi:application --bind 127.0.0.1:8001 --workers 3 > /tmp/gunicorn-test.log 2>&1 &"
else
    echo "⚠️  'test.campus-league.com' n'est PAS dans ALLOWED_HOSTS"
    echo ""
    echo "Ligne actuelle:"
    grep "ALLOWED_HOSTS" "$SETTINGS_FILE"
    echo ""

    # Créer une sauvegarde
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Sauvegarde créée: $SETTINGS_FILE.backup.*"
    echo ""

    # Ajouter test.campus-league.com à ALLOWED_HOSTS
    echo "🔄 Ajout de 'test.campus-league.com' à ALLOWED_HOSTS..."

    # Chercher la ligne ALLOWED_HOSTS et ajouter test.campus-league.com
    sed -i "s/ALLOWED_HOSTS = \[/ALLOWED_HOSTS = ['test.campus-league.com',/" "$SETTINGS_FILE"

    echo "✅ Modification effectuée"
    echo ""
    echo "Nouvelle configuration:"
    grep "ALLOWED_HOSTS" "$SETTINGS_FILE"
    echo ""

    # Redémarrer Gunicorn
    echo "🔄 Redémarrage de Gunicorn..."
    sudo pkill -9 -f "gunicorn.*8001"
    sleep 2

    cd /home/ubuntu/BDD-test/merchex
    nohup /home/ubuntu/BDD-test/venv-test/bin/gunicorn merchex.wsgi:application \
        --bind 127.0.0.1:8001 \
        --workers 3 \
        > /tmp/gunicorn-test.log 2>&1 &

    sleep 3
    echo "✅ Gunicorn redémarré"
    echo ""
fi

# Vérifier que Gunicorn tourne
echo "✔️  Vérification du processus Gunicorn..."
if ps aux | grep gunicorn | grep -v grep | grep 8001 > /dev/null; then
    echo "✅ Gunicorn est en cours d'exécution sur le port 8001"
    ps aux | grep gunicorn | grep -v grep | grep 8001 | head -1
else
    echo "❌ Gunicorn ne semble pas tourner"
    echo ""
    echo "Logs (10 dernières lignes):"
    tail -10 /tmp/gunicorn-test.log
    exit 1
fi
echo ""

# Tester un endpoint
echo "🧪 Test de l'endpoint /api/login/..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://test.campus-league.com/api/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' 2>&1)

echo "HTTP Status: $HTTP_CODE"

if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Le serveur répond correctement (pas d'erreur 400 DisallowedHost)"
else
    echo "⚠️  Réponse inattendue. Vérifiez les logs:"
    echo "  tail -20 /tmp/gunicorn-test.log"
fi
echo ""

echo "================================================"
echo "✅ CORRECTION TERMINÉE"
echo "================================================"
echo ""
echo "📝 Pour surveiller les logs:"
echo "  tail -f /tmp/gunicorn-test.log"
echo ""
