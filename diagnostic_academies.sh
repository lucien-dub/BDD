#!/bin/bash

echo "🔍 DIAGNOSTIC APPROFONDI - ENDPOINT ACADEMIES"
echo "=============================================="
echo ""

cd /home/ubuntu/BDD-test/merchex

echo "1️⃣ Test Django Shell - Résolution URL"
echo "========================================"
python3 manage.py shell << 'PYEOF'
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

# Test résolution de l'URL
try:
    match = resolve('/api/academies/available/')
    print(f"✅ URL trouvée: {match.url_name}")
    print(f"   Vue: {match.func.__module__}.{match.func.__name__}")
    print(f"   Args: {match.args}")
    print(f"   Kwargs: {match.kwargs}")
except Resolver404 as e:
    print(f"❌ URL NON TROUVÉE: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")

# Test reverse
try:
    url = reverse('available_academies')
    print(f"✅ Reverse OK: {url}")
except Exception as e:
    print(f"❌ Reverse échoue: {e}")

# Lister toutes les URLs avec 'academies'
from django.urls import get_resolver
resolver = get_resolver()
print("\n📋 URLs contenant 'academies':")
for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'academies' in pattern_str:
        print(f"   - {pattern_str}")
PYEOF

echo ""
echo "2️⃣ Test Import de la Vue"
echo "=========================="
python3 manage.py shell << 'PYEOF'
try:
    from listings.views import get_available_academies
    print(f"✅ Import réussi: {get_available_academies}")
    print(f"   Module: {get_available_academies.__module__}")
    print(f"   Décorateurs: {hasattr(get_available_academies, 'cls')}")
except ImportError as e:
    print(f"❌ Import échoue: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")
PYEOF

echo ""
echo "3️⃣ Test Appel Direct de la Vue"
echo "================================"
python3 manage.py shell << 'PYEOF'
from django.test import RequestFactory
from listings.views import get_available_academies
from django.contrib.auth.models import User

factory = RequestFactory()
request = factory.get('/api/academies/available/')

# Créer un utilisateur de test
try:
    user = User.objects.first()
    if user:
        request.user = user
        print(f"✅ Utilisateur: {user.username}")

        try:
            response = get_available_academies(request)
            print(f"✅ Vue appelée avec succès")
            print(f"   Status: {response.status_code}")
            print(f"   Data: {response.data}")
        except Exception as e:
            print(f"❌ Erreur lors de l'appel: {e}")
    else:
        print("⚠️  Aucun utilisateur dans la BD")
except Exception as e:
    print(f"❌ Erreur: {e}")
PYEOF

echo ""
echo "4️⃣ Comparaison avec sports (qui fonctionne)"
echo "============================================="
python3 manage.py shell << 'PYEOF'
from django.urls import resolve

try:
    match_sports = resolve('/api/sports/available/')
    match_academies = resolve('/api/academies/available/')

    print("Sports:")
    print(f"  Vue: {match_sports.func.__name__}")
    print(f"  Module: {match_sports.func.__module__}")

    print("\nAcademies:")
    print(f"  Vue: {match_academies.func.__name__}")
    print(f"  Module: {match_academies.func.__module__}")

    print("\n✅ Les deux URLs sont enregistrées")
except Exception as e:
    print(f"❌ Erreur: {e}")
PYEOF

echo ""
echo "5️⃣ Vérification Fichiers Python"
echo "=================================="
echo "Fichier views.py modifié:"
stat -c "Modifié: %y" listings/views.py

echo "Fichier urls.py modifié:"
stat -c "Modifié: %y" merchex/urls.py

echo ""
echo "Fichiers .pyc récents:"
find . -name "*.pyc" -mmin -30 -ls 2>/dev/null | head -5

echo ""
echo "6️⃣ Test HTTP Direct sur Django"
echo "================================"
python3 manage.py shell << 'PYEOF'
from django.test import Client
from django.contrib.auth.models import User

client = Client()
user = User.objects.first()

if user:
    # Login
    client.force_login(user)

    # Test academies
    response = client.get('/api/academies/available/')
    print(f"Academies - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Data: {response.json()}")
    else:
        print(f"❌ Content: {response.content}")

    # Test sports (pour comparer)
    response_sports = client.get('/api/sports/available/')
    print(f"\nSports - Status: {response_sports.status_code}")
    if response_sports.status_code == 200:
        print(f"✅ Data keys: {response_sports.json().keys()}")
else:
    print("❌ Aucun utilisateur disponible")
PYEOF

echo ""
echo "=============================================="
echo "✅ DIAGNOSTIC TERMINÉ"
echo "=============================================="
