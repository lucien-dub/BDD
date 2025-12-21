#!/bin/bash

echo "🔍 COMPARAISON SERVEUR NORMAL vs SERVEUR TEST"
echo "=============================================="
echo ""

echo "📋 1. CONFIGURATION NGINX"
echo "========================"
echo ""

echo "🟢 Serveur NORMAL (campus-league.com):"
echo "---------------------------------------"
if [ -f "/etc/nginx/sites-available/campus-league.com" ]; then
    cat /etc/nginx/sites-available/campus-league.com
else
    echo "⚠️  Fichier non trouvé"
fi

echo ""
echo ""
echo "🔵 Serveur TEST (test.campus-league.com):"
echo "---------------------------------------"
if [ -f "/etc/nginx/sites-enabled/test.campus-league.com" ] || [ -f "/etc/nginx/sites-available/test.campus-league.com" ]; then
    cat /etc/nginx/sites-enabled/test.campus-league.com 2>/dev/null || cat /etc/nginx/sites-available/test.campus-league.com 2>/dev/null
else
    echo "⚠️  Fichier non trouvé"
fi

echo ""
echo ""
echo "📋 2. PROCESSUS GUNICORN"
echo "========================"
echo ""

echo "Recherche de tous les processus Gunicorn:"
ps aux | grep gunicorn | grep -v grep

echo ""
echo ""
echo "📋 3. PORTS EN ÉCOUTE"
echo "====================="
echo ""

echo "Ports 8000 et 8001:"
sudo netstat -tlnp | grep -E ':(8000|8001)'

echo ""
echo ""
echo "📋 4. STRUCTURE DES RÉPERTOIRES"
echo "================================"
echo ""

echo "🟢 Serveur NORMAL:"
if [ -d "/home/ubuntu/BDD" ]; then
    echo "✅ /home/ubuntu/BDD existe"
    ls -la /home/ubuntu/BDD | head -15
else
    echo "❌ /home/ubuntu/BDD n'existe pas"
fi

echo ""
echo "🔵 Serveur TEST:"
if [ -d "/home/ubuntu/BDD-test" ]; then
    echo "✅ /home/ubuntu/BDD-test existe"
    ls -la /home/ubuntu/BDD-test | head -15
else
    echo "❌ /home/ubuntu/BDD-test n'existe pas"
fi

echo ""
echo ""
echo "📋 5. BRANCHES GIT"
echo "=================="
echo ""

echo "🟢 Serveur NORMAL:"
if [ -d "/home/ubuntu/BDD" ]; then
    cd /home/ubuntu/BDD
    echo "Branche actuelle: $(git branch --show-current)"
    echo "Dernier commit: $(git log -1 --oneline)"
fi

echo ""
echo "🔵 Serveur TEST:"
if [ -d "/home/ubuntu/BDD-test" ]; then
    cd /home/ubuntu/BDD-test
    echo "Branche actuelle: $(git branch --show-current)"
    echo "Dernier commit: $(git log -1 --oneline)"
fi

echo ""
echo ""
echo "📋 6. TEST DIRECT DES ENDPOINTS"
echo "================================"
echo ""

echo "🟢 Test serveur NORMAL (port 8000):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8000/api/academies/available/ -H "Authorization: Bearer test"

echo ""
echo "🔵 Test serveur TEST (port 8001):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8001/api/academies/available/ -H "Authorization: Bearer test"

echo ""
echo ""
echo "📋 7. VÉRIFICATION DES HEADERS CORS"
echo "===================================="
echo ""

echo "🟢 Headers serveur NORMAL:"
curl -I https://campus-league.com/api/academies/available/ -H "Origin: http://localhost:8100" 2>&1 | grep -i "access-control"

echo ""
echo "🔵 Headers serveur TEST:"
curl -I https://test.campus-league.com/api/academies/available/ -H "Origin: http://localhost:8100" 2>&1 | grep -i "access-control"

echo ""
echo ""
echo "=============================================="
echo "✅ DIAGNOSTIC TERMINÉ"
echo "=============================================="
