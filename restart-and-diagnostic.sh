#!/bin/bash

# ═══════════════════════════════════════════════════════════
# SCRIPT DE REDÉMARRAGE ET DIAGNOSTIC COMPLET
# Serveurs BDD (PRODUCTION) et BDD-test (TEST)
# ═══════════════════════════════════════════════════════════

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Variables des chemins
PROD_DIR="/home/ubuntu/BDD"
TEST_DIR="/home/ubuntu/BDD-test"
VENV_PROD="$PROD_DIR/venv"
VENV_TEST="$TEST_DIR/venv-websocket"

# Fonction d'affichage de section
print_section() {
    echo ""
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Fonction de statut
print_status() {
    if [ "$2" == "success" ]; then
        echo -e "${GREEN}✅ $1${NC}"
    elif [ "$2" == "warning" ]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    elif [ "$2" == "error" ]; then
        echo -e "${RED}❌ $1${NC}"
    elif [ "$2" == "info" ]; then
        echo -e "${BLUE}ℹ️  $1${NC}"
    else
        echo -e "$1"
    fi
}

echo ""
echo -e "${BOLD}${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${MAGENTA}  🔄 REDÉMARRAGE ET DIAGNOSTIC COMPLET DES SERVICES${NC}"
echo -e "${BOLD}${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""
date
echo ""

# ═══════════════════════════════════════════════════════════
# PARTIE 1: REDÉMARRAGE DES SERVICES
# ═══════════════════════════════════════════════════════════

print_section "PARTIE 1: REDÉMARRAGE DES SERVICES"

# 1.1 Arrêt de tous les services
echo -e "${YELLOW}[1/6] Arrêt de tous les services...${NC}"
echo ""

print_status "Arrêt de Nginx..." "info"
sudo systemctl stop nginx 2>/dev/null || print_status "Nginx n'était pas actif" "warning"
sleep 1

print_status "Arrêt de Gunicorn (PROD - port 8000)..." "info"
sudo pkill -f "gunicorn.*8000" 2>/dev/null || print_status "Aucun Gunicorn sur 8000" "warning"
sleep 1

print_status "Arrêt de Gunicorn (TEST - port 8001)..." "info"
sudo pkill -f "gunicorn.*8001" 2>/dev/null || print_status "Aucun Gunicorn sur 8001" "warning"
sleep 1

print_status "Arrêt de Daphne (WebSocket - port 8002)..." "info"
sudo pkill -f "daphne" 2>/dev/null || print_status "Aucun Daphne actif" "warning"
sleep 1

print_status "Arrêt de Redis..." "info"
redis-cli shutdown 2>/dev/null || print_status "Redis n'était pas actif" "warning"
sleep 2

echo ""
print_status "Tous les services ont été arrêtés" "success"
echo ""

# 1.2 Démarrage de Redis
echo -e "${YELLOW}[2/6] Démarrage de Redis...${NC}"
redis-server --daemonize yes --port 6379 2>/dev/null
sleep 2
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis démarré sur port 6379" "success"
else
    print_status "ERREUR: Redis n'a pas démarré" "error"
    exit 1
fi
echo ""

# 1.3 Démarrage Gunicorn PRODUCTION (port 8000)
echo -e "${YELLOW}[3/6] Démarrage de Gunicorn PRODUCTION (port 8000)...${NC}"
if [ -d "$PROD_DIR" ]; then
    cd $PROD_DIR/merchex

    # Activer l'environnement virtuel
    if [ -d "$VENV_PROD" ]; then
        source $VENV_PROD/bin/activate

        # Appliquer les migrations
        python manage.py migrate --noinput 2>/dev/null || true

        # Démarrer Gunicorn
        nohup gunicorn merchex.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers 3 \
            --timeout 120 \
            --access-logfile /tmp/gunicorn-prod-access.log \
            --error-logfile /tmp/gunicorn-prod-error.log \
            >> /tmp/gunicorn-prod.log 2>&1 &

        GUNICORN_PROD_PID=$!
        sleep 3

        if ps -p $GUNICORN_PROD_PID > /dev/null 2>&1; then
            print_status "Gunicorn PRODUCTION démarré (PID: $GUNICORN_PROD_PID)" "success"
        else
            print_status "Erreur au démarrage de Gunicorn PRODUCTION" "error"
        fi

        deactivate
    else
        print_status "Environnement virtuel non trouvé: $VENV_PROD" "warning"
    fi
else
    print_status "Répertoire non trouvé: $PROD_DIR" "warning"
fi
echo ""

# 1.4 Démarrage Gunicorn TEST (port 8001)
echo -e "${YELLOW}[4/6] Démarrage de Gunicorn TEST (port 8001)...${NC}"
if [ -d "$TEST_DIR" ]; then
    cd $TEST_DIR/merchex

    # Activer l'environnement virtuel
    if [ -d "$VENV_TEST" ]; then
        source $VENV_TEST/bin/activate

        # Appliquer les migrations
        python manage.py migrate --noinput 2>/dev/null || true

        # Démarrer Gunicorn
        nohup gunicorn merchex.wsgi:application \
            --bind 0.0.0.0:8001 \
            --workers 3 \
            --timeout 120 \
            --access-logfile /tmp/gunicorn-test-access.log \
            --error-logfile /tmp/gunicorn-test-error.log \
            >> /tmp/gunicorn-test.log 2>&1 &

        GUNICORN_TEST_PID=$!
        sleep 3

        if ps -p $GUNICORN_TEST_PID > /dev/null 2>&1; then
            print_status "Gunicorn TEST démarré (PID: $GUNICORN_TEST_PID)" "success"
        else
            print_status "Erreur au démarrage de Gunicorn TEST" "error"
        fi

        deactivate
    else
        print_status "Environnement virtuel non trouvé: $VENV_TEST" "warning"
    fi
else
    print_status "Répertoire non trouvé: $TEST_DIR" "warning"
fi
echo ""

# 1.5 Démarrage Daphne (WebSocket - port 8002)
echo -e "${YELLOW}[5/6] Démarrage de Daphne pour WebSocket (port 8002)...${NC}"
if [ -d "$TEST_DIR" ]; then
    cd $TEST_DIR/merchex

    if [ -d "$VENV_TEST" ]; then
        source $VENV_TEST/bin/activate

        # Démarrer Daphne
        nohup daphne -b 0.0.0.0 -p 8002 merchex.asgi:application \
            >> /tmp/daphne-test.log 2>&1 &

        DAPHNE_PID=$!
        sleep 3

        if ps -p $DAPHNE_PID > /dev/null 2>&1; then
            print_status "Daphne démarré (PID: $DAPHNE_PID)" "success"
        else
            print_status "Erreur au démarrage de Daphne" "error"
            echo "Logs Daphne:"
            tail -10 /tmp/daphne-test.log 2>/dev/null
        fi

        deactivate
    fi
else
    print_status "Répertoire non trouvé pour Daphne" "warning"
fi
echo ""

# 1.6 Démarrage de Nginx
echo -e "${YELLOW}[6/6] Démarrage de Nginx...${NC}"

# Tester la configuration avant de démarrer
sudo nginx -t 2>&1 | head -5

if sudo nginx -t 2>&1 | grep -q "successful"; then
    sudo systemctl start nginx
    sleep 2

    if sudo systemctl is-active --quiet nginx; then
        print_status "Nginx démarré avec succès" "success"
    else
        print_status "Erreur au démarrage de Nginx" "error"
    fi
else
    print_status "Configuration Nginx invalide - Nginx non démarré" "error"
fi
echo ""

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ REDÉMARRAGE DES SERVICES TERMINÉ               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
sleep 2

# ═══════════════════════════════════════════════════════════
# PARTIE 2: DIAGNOSTIC COMPLET
# ═══════════════════════════════════════════════════════════

print_section "PARTIE 2: DIAGNOSTIC COMPLET"

# 2.1 Informations système
print_section "2.1 - INFORMATIONS SYSTÈME"
hostname
uname -a
echo ""
uptime
echo ""

# 2.2 État des processus
print_section "2.2 - ÉTAT DES PROCESSUS"

echo -e "${BOLD}Redis:${NC}"
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis: ACTIF ($(redis-cli ping))" "success"
    redis-cli INFO server | grep redis_version
else
    print_status "Redis: INACTIF" "error"
fi
echo ""

echo -e "${BOLD}Gunicorn PRODUCTION (port 8000):${NC}"
ps aux | grep "gunicorn.*8000" | grep -v grep || print_status "Aucun processus Gunicorn sur port 8000" "warning"
echo ""

echo -e "${BOLD}Gunicorn TEST (port 8001):${NC}"
ps aux | grep "gunicorn.*8001" | grep -v grep || print_status "Aucun processus Gunicorn sur port 8001" "warning"
echo ""

echo -e "${BOLD}Daphne (port 8002):${NC}"
ps aux | grep daphne | grep -v grep || print_status "Aucun processus Daphne" "warning"
echo ""

echo -e "${BOLD}Nginx:${NC}"
if sudo systemctl is-active --quiet nginx; then
    print_status "Nginx: ACTIF" "success"
    sudo systemctl status nginx --no-pager | head -10
else
    print_status "Nginx: INACTIF" "error"
fi
echo ""

# 2.3 Ports en écoute
print_section "2.3 - PORTS EN ÉCOUTE"

echo -e "${BOLD}Ports Django (8000, 8001) et WebSocket (8002):${NC}"
sudo netstat -tlnp | grep -E ':(8000|8001|8002)' || print_status "Aucun processus sur ces ports" "warning"
echo ""

echo -e "${BOLD}Port Redis (6379):${NC}"
sudo netstat -tlnp | grep ':6379' || print_status "Redis non en écoute" "warning"
echo ""

echo -e "${BOLD}Ports HTTP/HTTPS (80, 443):${NC}"
sudo netstat -tlnp | grep -E ':(80|443)' || print_status "Nginx non en écoute" "warning"
echo ""

# 2.4 Configurations Nginx
print_section "2.4 - CONFIGURATIONS NGINX"

echo -e "${BOLD}📁 Fichiers disponibles:${NC}"
ls -la /etc/nginx/sites-available/ | grep campus || print_status "Aucun fichier campus trouvé" "warning"
echo ""

echo -e "${BOLD}🔗 Fichiers actifs (liens symboliques):${NC}"
ls -la /etc/nginx/sites-enabled/ | grep campus || print_status "Aucun fichier campus actif" "warning"
echo ""

echo -e "${BOLD}📄 Configuration PRODUCTION (campus-league.com):${NC}"
if [ -f "/etc/nginx/sites-available/campus-league.com" ]; then
    cat /etc/nginx/sites-available/campus-league.com
else
    print_status "Fichier non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 Configuration TEST (test.campus-league.com):${NC}"
if [ -f "/etc/nginx/sites-available/test.campus-league.com" ]; then
    cat /etc/nginx/sites-available/test.campus-league.com
elif [ -f "/etc/nginx/sites-enabled/test.campus-league.com" ]; then
    cat /etc/nginx/sites-enabled/test.campus-league.com
else
    print_status "Fichier non trouvé" "warning"
fi
echo ""

# 2.5 État des répertoires
print_section "2.5 - ÉTAT DES RÉPERTOIRES"

echo -e "${BOLD}📁 PRODUCTION (/home/ubuntu/BDD):${NC}"
if [ -d "$PROD_DIR" ]; then
    print_status "Répertoire existe" "success"
    cd $PROD_DIR
    echo "Branche Git: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    echo "Dernier commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo "Fichiers:"
    ls -lah | head -15
    echo ""
    echo "Environnement virtuel:"
    ls -d venv* 2>/dev/null || print_status "Aucun venv trouvé" "warning"
else
    print_status "Répertoire n'existe pas" "error"
fi
echo ""

echo -e "${BOLD}📁 TEST (/home/ubuntu/BDD-test):${NC}"
if [ -d "$TEST_DIR" ]; then
    print_status "Répertoire existe" "success"
    cd $TEST_DIR
    echo "Branche Git: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    echo "Dernier commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo "Fichiers:"
    ls -lah | head -15
    echo ""
    echo "Environnement virtuel:"
    ls -d venv* 2>/dev/null || print_status "Aucun venv trouvé" "warning"
else
    print_status "Répertoire n'existe pas" "error"
fi
echo ""

# 2.6 Configuration Django
print_section "2.6 - CONFIGURATION DJANGO"

echo -e "${BOLD}📄 PRODUCTION - ALLOWED_HOSTS:${NC}"
if [ -f "$PROD_DIR/merchex/merchex/settings.py" ]; then
    grep -A 2 "ALLOWED_HOSTS" $PROD_DIR/merchex/merchex/settings.py
else
    print_status "Fichier settings.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 TEST - ALLOWED_HOSTS:${NC}"
if [ -f "$TEST_DIR/merchex/merchex/settings.py" ]; then
    grep -A 2 "ALLOWED_HOSTS" $TEST_DIR/merchex/merchex/settings.py
else
    print_status "Fichier settings.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 PRODUCTION - CORS Configuration:${NC}"
if [ -f "$PROD_DIR/merchex/merchex/settings.py" ]; then
    grep -A 5 "CORS" $PROD_DIR/merchex/merchex/settings.py | head -20
else
    print_status "Fichier settings.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 TEST - CORS Configuration:${NC}"
if [ -f "$TEST_DIR/merchex/merchex/settings.py" ]; then
    grep -A 5 "CORS" $TEST_DIR/merchex/merchex/settings.py | head -20
else
    print_status "Fichier settings.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 TEST - WebSocket Configuration:${NC}"
if [ -f "$TEST_DIR/merchex/merchex/settings.py" ]; then
    grep -A 10 "CHANNEL\|ASGI" $TEST_DIR/merchex/merchex/settings.py | head -30
else
    print_status "Fichier settings.py non trouvé" "warning"
fi
echo ""

# 2.7 Tests des endpoints
print_section "2.7 - TESTS DES ENDPOINTS"

echo -e "${BOLD}🧪 Test direct PRODUCTION (port 8000):${NC}"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8000/api/academies/available/ 2>/dev/null || print_status "Impossible de se connecter" "error"
echo ""

echo -e "${BOLD}🧪 Test direct TEST (port 8001):${NC}"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8001/api/academies/available/ 2>/dev/null || print_status "Impossible de se connecter" "error"
echo ""

echo -e "${BOLD}🧪 Test WebSocket Daphne (port 8002):${NC}"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://127.0.0.1:8002/api/academies/available/ 2>/dev/null || print_status "Impossible de se connecter" "error"
echo ""

echo -e "${BOLD}🌐 Test HTTPS PRODUCTION (campus-league.com):${NC}"
curl -s -I https://campus-league.com/api/academies/available/ 2>&1 | head -10
echo ""

echo -e "${BOLD}🌐 Test HTTPS TEST (test.campus-league.com):${NC}"
curl -s -I https://test.campus-league.com/api/academies/available/ 2>&1 | head -10
echo ""

echo -e "${BOLD}🔌 Test WebSocket Connection:${NC}"
curl -s -I https://test.campus-league.com/ws/cotes/ 2>&1 | head -10
echo ""

# 2.8 Headers CORS
print_section "2.8 - VÉRIFICATION DES HEADERS CORS"

echo -e "${BOLD}🔐 CORS Headers PRODUCTION:${NC}"
curl -I https://campus-league.com/api/academies/available/ -H "Origin: http://localhost:8100" 2>&1 | grep -i "access-control" || print_status "Aucun header CORS" "warning"
echo ""

echo -e "${BOLD}🔐 CORS Headers TEST:${NC}"
curl -I https://test.campus-league.com/api/academies/available/ -H "Origin: http://localhost:8100" 2>&1 | grep -i "access-control" || print_status "Aucun header CORS" "warning"
echo ""

# 2.9 Logs récents
print_section "2.9 - LOGS RÉCENTS"

echo -e "${BOLD}📋 Nginx Error Log (20 dernières lignes):${NC}"
sudo tail -20 /var/log/nginx/error.log 2>/dev/null || print_status "Log non accessible" "warning"
echo ""

echo -e "${BOLD}📋 Gunicorn PRODUCTION (10 dernières lignes):${NC}"
tail -10 /tmp/gunicorn-prod-error.log 2>/dev/null || print_status "Log non trouvé" "warning"
echo ""

echo -e "${BOLD}📋 Gunicorn TEST (10 dernières lignes):${NC}"
tail -10 /tmp/gunicorn-test-error.log 2>/dev/null || print_status "Log non trouvé" "warning"
echo ""

echo -e "${BOLD}📋 Daphne WebSocket (10 dernières lignes):${NC}"
tail -10 /tmp/daphne-test.log 2>/dev/null || print_status "Log non trouvé" "warning"
echo ""

echo -e "${BOLD}📋 Redis Log:${NC}"
redis-cli INFO stats | grep -E "total_connections_received|total_commands_processed|keyspace" 2>/dev/null || print_status "Stats Redis non disponibles" "warning"
echo ""

# 2.10 État détaillé des services systemd
print_section "2.10 - ÉTAT DES SERVICES SYSTEMD"

echo -e "${BOLD}Nginx:${NC}"
sudo systemctl status nginx --no-pager -l 2>/dev/null || print_status "Statut non disponible" "warning"
echo ""

echo -e "${BOLD}Services Gunicorn (si configurés):${NC}"
sudo systemctl list-units --type=service | grep gunicorn || print_status "Aucun service Gunicorn systemd trouvé" "info"
echo ""

echo -e "${BOLD}Services Daphne (si configurés):${NC}"
sudo systemctl list-units --type=service | grep daphne || print_status "Aucun service Daphne systemd trouvé" "info"
echo ""

# 2.11 Vérification des endpoints dans le code
print_section "2.11 - ENDPOINTS DÉFINIS DANS LE CODE"

echo -e "${BOLD}📄 PRODUCTION - URLs principales:${NC}"
if [ -f "$PROD_DIR/merchex/merchex/urls.py" ]; then
    grep -n "path\|re_path" $PROD_DIR/merchex/merchex/urls.py | head -30
else
    print_status "Fichier urls.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 TEST - URLs principales:${NC}"
if [ -f "$TEST_DIR/merchex/merchex/urls.py" ]; then
    grep -n "path\|re_path" $TEST_DIR/merchex/merchex/urls.py | head -30
else
    print_status "Fichier urls.py non trouvé" "warning"
fi
echo ""

echo -e "${BOLD}📄 TEST - Routing WebSocket (asgi.py):${NC}"
if [ -f "$TEST_DIR/merchex/merchex/asgi.py" ]; then
    cat $TEST_DIR/merchex/merchex/asgi.py
else
    print_status "Fichier asgi.py non trouvé" "warning"
fi
echo ""

# 2.12 Résumé final
print_section "2.12 - RÉSUMÉ FINAL"

echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║              RÉSUMÉ DE L'ÉTAT DES SERVICES               ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Redis:${NC}           ACTIF (port 6379)"
else
    echo -e "  ${RED}❌ Redis:${NC}           INACTIF"
fi

# Gunicorn PROD
if ps aux | grep -q "[g]unicorn.*8000"; then
    echo -e "  ${GREEN}✅ Gunicorn PROD:${NC}   ACTIF (port 8000)"
else
    echo -e "  ${RED}❌ Gunicorn PROD:${NC}   INACTIF"
fi

# Gunicorn TEST
if ps aux | grep -q "[g]unicorn.*8001"; then
    echo -e "  ${GREEN}✅ Gunicorn TEST:${NC}   ACTIF (port 8001)"
else
    echo -e "  ${RED}❌ Gunicorn TEST:${NC}   INACTIF"
fi

# Daphne
if ps aux | grep -q "[d]aphne"; then
    echo -e "  ${GREEN}✅ Daphne:${NC}          ACTIF (port 8002)"
else
    echo -e "  ${RED}❌ Daphne:${NC}          INACTIF"
fi

# Nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "  ${GREEN}✅ Nginx:${NC}           ACTIF (ports 80/443)"
else
    echo -e "  ${RED}❌ Nginx:${NC}           INACTIF"
fi

echo ""
echo -e "${BOLD}${BLUE}📝 Commandes utiles:${NC}"
echo ""
echo "  • Voir logs Gunicorn PROD:   tail -f /tmp/gunicorn-prod-error.log"
echo "  • Voir logs Gunicorn TEST:   tail -f /tmp/gunicorn-test-error.log"
echo "  • Voir logs Daphne:          tail -f /tmp/daphne-test.log"
echo "  • Voir logs Nginx:           sudo tail -f /var/log/nginx/error.log"
echo "  • Test Redis:                redis-cli ping"
echo "  • Redémarrer Nginx:          sudo systemctl restart nginx"
echo ""

echo ""
echo -e "${BOLD}${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${MAGENTA}  ✅ DIAGNOSTIC COMPLET TERMINÉ${NC}"
echo -e "${BOLD}${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""
date
echo ""
