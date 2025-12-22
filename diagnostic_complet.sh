#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC COMPLET SERVEUR NORMAL vs SERVEUR TEST"
echo "═══════════════════════════════════════════════════════════"
echo ""
date
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. INFORMATIONS SYSTÈME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
hostname
uname -a
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. PROCESSUS GUNICORN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Tous les processus Gunicorn:"
ps aux | grep gunicorn | grep -v grep || echo "Aucun processus Gunicorn"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. PORTS EN ÉCOUTE (8000 et 8001)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sudo netstat -tlnp | grep -E ':(8000|8001)' || echo "Aucun processus sur les ports 8000/8001"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. CONFIGURATIONS NGINX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📁 Fichiers de configuration disponibles:"
ls -la /etc/nginx/sites-available/ | grep campus
echo ""

echo "🔗 Fichiers de configuration actifs:"
ls -la /etc/nginx/sites-enabled/ | grep campus
echo ""

echo "📄 Configuration pour campus-league.com:"
if [ -f "/etc/nginx/sites-available/campus-league.com" ]; then
    cat /etc/nginx/sites-available/campus-league.com
else
    echo "Fichier non trouvé"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. RÉPERTOIRES DES PROJETS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📁 Serveur NORMAL (/home/ubuntu/BDD):"
if [ -d "/home/ubuntu/BDD" ]; then
    echo "✅ Existe"
    cd /home/ubuntu/BDD
    echo "Branche Git: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    echo "Dernier commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo "Répertoire merchex: $([ -d merchex ] && echo '✅' || echo '❌')"
    echo "Fichier wsgi.py: $([ -f merchex/merchex/wsgi.py ] && echo '✅' || echo '❌')"
else
    echo "❌ N'existe pas"
fi
echo ""

echo "📁 Serveur TEST (/home/ubuntu/BDD-test):"
if [ -d "/home/ubuntu/BDD-test" ]; then
    echo "✅ Existe"
    cd /home/ubuntu/BDD-test
    echo "Branche Git: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    echo "Dernier commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo "Répertoire merchex: $([ -d merchex ] && echo '✅' || echo '❌')"
    echo "Fichier wsgi.py: $([ -f merchex/merchex/wsgi.py ] && echo '✅' || echo '❌')"
else
    echo "❌ N'existe pas"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. FICHIERS IMPORTANTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📄 Serveur NORMAL - ALLOWED_HOSTS:"
if [ -f "/home/ubuntu/BDD/merchex/merchex/settings.py" ]; then
    grep "ALLOWED_HOSTS" /home/ubuntu/BDD/merchex/merchex/settings.py
else
    echo "Fichier non trouvé"
fi
echo ""

echo "📄 Serveur TEST - ALLOWED_HOSTS:"
if [ -f "/home/ubuntu/BDD-test/merchex/merchex/settings.py" ]; then
    grep "ALLOWED_HOSTS" /home/ubuntu/BDD-test/merchex/merchex/settings.py
else
    echo "Fichier non trouvé"
fi
echo ""

echo "📄 Serveur NORMAL - CORS Configuration:"
if [ -f "/home/ubuntu/BDD/merchex/merchex/settings.py" ]; then
    grep -A 5 "CORS" /home/ubuntu/BDD/merchex/merchex/settings.py | head -20
else
    echo "Fichier non trouvé"
fi
echo ""

echo "📄 Serveur TEST - CORS Configuration:"
if [ -f "/home/ubuntu/BDD-test/merchex/merchex/settings.py" ]; then
    grep -A 5 "CORS" /home/ubuntu/BDD-test/merchex/merchex/settings.py | head -20
else
    echo "Fichier non trouvé"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. ENVIRONNEMENTS VIRTUELS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📦 Serveur NORMAL:"
if [ -d "/home/ubuntu/BDD" ]; then
    cd /home/ubuntu/BDD
    ls -d venv* 2>/dev/null || echo "Aucun environnement virtuel trouvé"
fi
echo ""

echo "📦 Serveur TEST:"
if [ -d "/home/ubuntu/BDD-test" ]; then
    cd /home/ubuntu/BDD-test
    ls -d venv* 2>/dev/null || echo "Aucun environnement virtuel trouvé"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. TESTS DIRECTS DES ENDPOINTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🧪 Test port 8000 (Serveur NORMAL):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8000/api/academies/available/ 2>/dev/null || echo "Impossible de se connecter"
echo ""

echo "🧪 Test port 8001 (Serveur TEST):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8001/api/academies/available/ 2>/dev/null || echo "Impossible de se connecter"
echo ""

echo "🧪 Test HTTPS campus-league.com:"
curl -s -I https://campus-league.com/api/academies/available/ 2>&1 | head -15
echo ""

echo "🧪 Test HTTPS test.campus-league.com:"
curl -s -I https://test.campus-league.com/api/academies/available/ 2>&1 | head -15
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. LOGS RÉCENTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Nginx Error Log (dernières 10 lignes):"
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "Log non accessible"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "10. VÉRIFICATION DES ENDPOINTS DANS LE CODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📄 Serveur NORMAL - Endpoints dans urls.py:"
if [ -f "/home/ubuntu/BDD/merchex/merchex/urls.py" ]; then
    grep -n "academies/available" /home/ubuntu/BDD/merchex/merchex/urls.py || echo "Endpoint non trouvé"
    grep -n "sports/available" /home/ubuntu/BDD/merchex/merchex/urls.py || echo "Endpoint non trouvé"
    grep -n "matches/filtered" /home/ubuntu/BDD/merchex/merchex/urls.py || echo "Endpoint non trouvé"
else
    echo "Fichier non trouvé"
fi
echo ""

echo "📄 Serveur TEST - Endpoints dans urls.py:"
if [ -f "/home/ubuntu/BDD-test/merchex/merchex/urls.py" ]; then
    grep -n "academies/available" /home/ubuntu/BDD-test/merchex/merchex/urls.py || echo "Endpoint non trouvé"
    grep -n "sports/available" /home/ubuntu/BDD-test/merchex/merchex/urls.py || echo "Endpoint non trouvé"
    grep -n "matches/filtered" /home/ubuntu/BDD-test/merchex/merchex/urls.py || echo "Endpoint non trouvé"
else
    echo "Fichier non trouvé"
fi
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "  FIN DU DIAGNOSTIC"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "💡 Pour partager ce diagnostic avec Claude, copiez toute la sortie"
echo ""
