# Instructions de Déploiement - Serveur Test

## Modifications effectuées

### Amélioration du filtrage des matchs

**Fichier modifié**: `merchex/listings/views.py`

**Endpoints améliorés**:

1. **`/api/results/filtered/`** (lignes 1374-1420)
   - Filtre STRICTEMENT les matchs terminés
   - Critères: `match_joue=True` ET `score1` ET `score2` non null
   - Ajout de la pagination (page, page_size)
   - Tri par date décroissante (plus récents en premier)

2. **`/api/matches/filtered/`** (lignes 1315-1371)
   - Filtre STRICTEMENT les matchs non commencés
   - Critères: `match_joue=False` ET (pas de scores OU scores à 0)
   - Pagination déjà présente
   - Tri par date croissante (prochains matchs en premier)

3. **Filtrage par académie**
   - Les deux endpoints supportent le paramètre `academie`
   - Permet de filtrer les résultats par académie spécifique

## Déploiement sur le serveur test

### Option 1: Script automatique

```bash
# Sur le serveur (via SSH)
cd /home/user/BDD
sudo bash deploy_to_test.sh
```

### Option 2: Commandes manuelles

```bash
# 1. Se connecter au serveur
ssh ubuntu@test.campus-league.com

# 2. Aller dans le répertoire test
cd /home/ubuntu/BDD-test

# 3. Pull les changements
git stash  # Sauvegarder les changements locaux éventuels
git pull origin claude/add-all-users-bets-endpoint-01UPVCBx4Kmz3Hip1vfxLrL9

# 4. Nettoyer le cache Python
sudo find merchex -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
sudo find merchex -name "*.pyc" -delete 2>/dev/null

# 5. Redémarrer Gunicorn
sudo pkill -9 -f "gunicorn.*8001"
cd /home/ubuntu/BDD-test/merchex

# Déterminer le venv (venv-test, venv-myapp, ou venv-bdd)
VENV_PATH="/home/ubuntu/BDD-test/venv-myapp"  # Ajuster si nécessaire

nohup $VENV_PATH/bin/gunicorn merchex.wsgi:application \
  --bind 127.0.0.1:8001 \
  --workers 3 \
  > /tmp/gunicorn-test.log 2>&1 &

# 6. Vérifier que Gunicorn tourne
ps aux | grep gunicorn | grep 8001
```

## Tests des endpoints

### Test 1: Matchs terminés (Results)

```bash
# Sans authentification (devrait retourner 401)
curl -I https://test.campus-league.com/api/results/filtered/?page=1&page_size=10

# Avec authentification
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/results/filtered/?page=1&page_size=10"

# Filtrage par académie
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/results/filtered/?academie=Ile-de-France&page=1&page_size=10"
```

### Test 2: Matchs à venir (Matches)

```bash
# Sans authentification (devrait retourner 401)
curl -I https://test.campus-league.com/api/matches/filtered/?page=1&page_size=15

# Avec authentification
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/matches/filtered/?page=1&page_size=15"

# Filtrage par académie et sport
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/matches/filtered/?academie=Ile-de-France&sport=Football&page=1"
```

### Test 3: Académies disponibles

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://test.campus-league.com/api/available-academies/
```

### Test 4: Sports disponibles

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://test.campus-league.com/api/sports/available/
```

## Vérification des logs

```bash
# Voir les logs en temps réel
tail -f /tmp/gunicorn-test.log

# Voir les dernières erreurs
tail -100 /tmp/gunicorn-test.log | grep -i error

# Vérifier les logs Nginx
sudo tail -50 /var/log/nginx/error.log
```

## Résolution de problèmes

### Gunicorn ne démarre pas

```bash
# Vérifier si le port 8001 est déjà utilisé
sudo netstat -tlnp | grep 8001

# Tuer tous les processus Gunicorn
sudo pkill -9 gunicorn

# Vérifier les logs
tail -50 /tmp/gunicorn-test.log
```

### Endpoint retourne 404

```bash
# Vérifier que les changements sont bien présents
cd /home/ubuntu/BDD-test/merchex
grep -n "def get_filtered_results" listings/views.py
grep -n "api/results/filtered" merchex/urls.py

# Nettoyer complètement le cache
sudo find . -type d -name "__pycache__" -delete
sudo find . -name "*.pyc" -delete
sudo pkill -9 gunicorn
# Puis redémarrer Gunicorn
```

### CORS errors

Les CORS sont gérés par `django-cors-headers` dans le middleware Django. Nginx passe simplement les headers.

Vérifier dans `merchex/settings.py`:
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
```

## Paramètres de requête supportés

### `/api/results/filtered/`
- `academie`: Nom de l'académie (ou "all")
- `sport`: Nom du sport (ou "all")
- `page`: Numéro de page (défaut: 1)
- `page_size`: Nombre de résultats par page (défaut: 50)

### `/api/matches/filtered/`
- `academie`: Nom de l'académie (ou "all")
- `sport`: Nom du sport (ou "all")
- `niveau`: Niveau du match (ou "all")
- `page`: Numéro de page (défaut: 1)
- `page_size`: Nombre de résultats par page (défaut: 15)

## Exemple de réponse

### `/api/results/filtered/`

```json
{
  "count": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 123,
      "date": "2024-01-15",
      "heure": "14:00:00",
      "academie": "Ile-de-France",
      "sport": "Football",
      "equipe1": "Team A",
      "equipe2": "Team B",
      "score1": 2,
      "score2": 1,
      "match_joue": true
    }
  ]
}
```

### `/api/matches/filtered/`

```json
{
  "count": 45,
  "page": 1,
  "page_size": 15,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 456,
      "date": "2024-02-01",
      "heure": "15:00:00",
      "academie": "Ile-de-France",
      "sport": "Basketball",
      "equipe1": "Team C",
      "equipe2": "Team D",
      "score1": null,
      "score2": null,
      "match_joue": false
    }
  ]
}
```

## Commit et branche

- **Branche**: `claude/add-all-users-bets-endpoint-01UPVCBx4Kmz3Hip1vfxLrL9`
- **Commit**: `0ec80ea4` - "fix: améliorer filtrage strict des matchs terminés vs à venir"
- **Fichiers modifiés**: `merchex/listings/views.py`
