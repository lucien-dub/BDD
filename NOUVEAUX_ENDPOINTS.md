# 📋 Nouveaux Endpoints Backend - Sports et Matchs

## ✅ Endpoints Implémentés

### 1. **Sports avec Niveaux**
**URL** : `/api/sports/with-levels/`
**Méthode** : `GET`
**Auth** : Requise (JWT Bearer Token)

Retourne tous les sports disponibles avec leurs niveaux respectifs.

**Exemple de requête** :
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://test.campus-league.com/api/sports/with-levels/
```

**Réponse attendue** :
```json
{
  "sports": [
    {
      "sport": "Basketball",
      "niveaux": ["Lycée", "Post-Bac", "Universitaire"]
    },
    {
      "sport": "Football",
      "niveaux": ["Collège", "Lycée", "Post-Bac", "Universitaire"]
    },
    {
      "sport": "Handball",
      "niveaux": ["Lycée", "Universitaire"]
    }
  ],
  "count": 3
}
```

---

### 2. **Tous les Matchs Futurs**
**URL** : `/api/matches/all-future/`
**Méthode** : `GET`
**Auth** : Requise (JWT Bearer Token)

Retourne TOUS les matchs futurs sans pagination (limité à 1000 matchs max).

**Paramètres query** :
- `academie` (optionnel) : Filtrer par académie
- `sport` (optionnel) : Filtrer par sport
- `niveau` (optionnel) : Filtrer par niveau

**Exemple de requête** :
```bash
# Sans filtre
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://test.campus-league.com/api/matches/all-future/

# Avec filtres
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/matches/all-future/?academie=Toulouse&sport=Football"
```

**Réponse attendue** :
```json
{
  "matches": [
    {
      "id": 12534,
      "equipe1": "UTCAP3",
      "equipe2": "TSE1",
      "date": "2026-01-05",
      "heure": "21:00:00",
      "academie": "Toulouse",
      "sport": "Football",
      "niveau": "Universitaire",
      "score1": null,
      "score2": null,
      "match_joue": false,
      "lieu": "Stade Municipal",
      "forfait_1": false,
      "forfait_2": false
    }
    // ... autres matchs
  ],
  "count": 456,
  "total_available": 500,
  "filters": {
    "academie": "Toulouse",
    "sport": "Football",
    "niveau": "all"
  }
}
```

---

## 📂 Fichiers Modifiés

1. **`/merchex/listings/views.py`**
   - Ajout de la fonction `sports_with_levels()`
   - Ajout de la fonction `all_future_matches()`

2. **`/merchex/merchex/urls.py`**
   - Ajout de la route `/api/sports/with-levels/`
   - Ajout de la route `/api/matches/all-future/`

---

## 🚀 Déploiement

### Sur le serveur TEST (test.campus-league.com)

```bash
# 1. Se connecter au serveur
ssh ubuntu@test.campus-league.com

# 2. Naviguer vers le projet
cd /home/ubuntu/BDD-test

# 3. Pull les dernières modifications
git pull origin claude/add-decimal-import-9S6bC

# 4. Redémarrer Gunicorn TEST
cd merchex
source ../venv-test/bin/activate

# Tuer l'ancien processus
pkill -f "gunicorn.*8001"

# Relancer Gunicorn
nohup gunicorn --workers 3 --bind 0.0.0.0:8001 \
  --timeout 120 \
  --access-logfile /tmp/gunicorn-test-access.log \
  --error-logfile /tmp/gunicorn-test-error.log \
  merchex.wsgi:application >> /tmp/gunicorn-test.log 2>&1 &

# 5. Vérifier que ça fonctionne
curl -H "Authorization: Bearer VOTRE_TOKEN" \
  https://test.campus-league.com/api/sports/with-levels/
```

### OU utiliser le script de redémarrage

```bash
cd /home/ubuntu/BDD-test
sudo ./restart-and-diagnostic.sh
```

---

## ✅ Tests

### Test de l'endpoint sports avec niveaux

```bash
curl -H "Authorization: Bearer VOTRE_TOKEN" \
  https://test.campus-league.com/api/sports/with-levels/ | jq
```

### Test de tous les matchs futurs

```bash
# Sans filtre
curl -H "Authorization: Bearer VOTRE_TOKEN" \
  https://test.campus-league.com/api/matches/all-future/ | jq

# Avec filtres
curl -H "Authorization: Bearer VOTRE_TOKEN" \
  "https://test.campus-league.com/api/matches/all-future/?sport=Football&niveau=Universitaire" | jq
```

---

## 🔍 Caractéristiques Techniques

### Filtrage des matchs futurs

Les deux endpoints utilisent la même logique pour déterminer si un match est "futur" :

1. **Date/Heure** : Le match est après maintenant (timezone Europe/Paris)
2. **Scores** : Les scores sont nuls ou tous deux à 0
3. **Exclusion** : Les matchs déjà terminés sont exclus

### Performance

- **`sports_with_levels`** : Rapide, traite tous les matchs futurs en mémoire
- **`all_future_matches`** : Limité à 1000 matchs pour éviter les réponses trop lourdes
- Les deux utilisent le serializer Django existant (`MatchSerializer`)

### Sécurité

- Les deux endpoints nécessitent l'authentification JWT
- Gestion d'erreurs avec try/except
- Logging des erreurs avec `logger.error()`

---

## ⚠️ Notes Importantes

1. **Limite de résultats** : L'endpoint `/api/matches/all-future/` est limité à 1000 matchs maximum pour éviter les réponses trop volumineuses.

2. **Timezone** : Tous les filtres de date/heure utilisent le timezone **Europe/Paris**.

3. **Cache** : Pour améliorer les performances en production, considérer l'ajout de cache :
   ```python
   from django.views.decorators.cache import cache_page

   @cache_page(60 * 5)  # Cache 5 minutes
   @api_view(['GET'])
   def sports_with_levels(request):
       # ...
   ```

4. **CORS** : Si problèmes CORS, vérifier `settings.py` :
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:8100",
       "https://test.campus-league.com",
       "https://campus-league.com"
   ]
   ```

---

## 📝 Exemples d'Utilisation Frontend

### Récupérer les sports et niveaux pour un formulaire

```typescript
async function getSportsWithLevels() {
  const response = await fetch(
    'https://test.campus-league.com/api/sports/with-levels/',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const data = await response.json();

  // data.sports = [
  //   { sport: "Football", niveaux: ["Lycée", "Universitaire"] },
  //   ...
  // ]

  return data.sports;
}
```

### Récupérer tous les matchs d'un sport

```typescript
async function getAllFootballMatches() {
  const response = await fetch(
    'https://test.campus-league.com/api/matches/all-future/?sport=Football',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const data = await response.json();

  // data.matches = [...]
  // data.count = nombre de matchs retournés

  return data.matches;
}
```
