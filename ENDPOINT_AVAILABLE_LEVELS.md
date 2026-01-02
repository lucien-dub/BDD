# 📋 Endpoint Available Levels - Documentation

## 🎯 Objectif

Endpoint permettant de récupérer les niveaux disponibles pour une combinaison académie + sport.

---

## 📡 Endpoint

### URL
```
GET /api/available-levels/
```

### Authentification
Requise (JWT Bearer Token)

### Paramètres Query

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `academie` | string | ✅ Oui | L'académie sélectionnée (ex: "Paris", "Toulouse") |
| `sport` | string | ✅ Oui | Le sport sélectionné (ex: "Football", "Basketball") |

### Réponse Succès (200)

```json
{
  "levels": ["U15", "U17", "U19", "Senior"],
  "count": 4
}
```

### Réponse Erreur (400)

```json
{
  "error": "Les paramètres academie et sport sont requis"
}
```

### Réponse Erreur (500)

```json
{
  "error": "Erreur lors de la récupération des niveaux",
  "details": "Message d'erreur détaillé"
}
```

---

## 🔍 Fonctionnement

### Filtres Appliqués

L'endpoint récupère les niveaux en filtrant les matchs selon ces critères :

1. **Matchs futurs uniquement**
   - Date > aujourd'hui OU (Date = aujourd'hui ET Heure >= maintenant)
   - Scores nuls ou à 0

2. **Académie**
   - Utilise `iexact` (insensible à la casse)
   - Ex: "paris" matche "Paris"

3. **Sport**
   - Utilise `icontains` (recherche partielle)
   - Ex: "Football" matche "Football Masc" ET "Football Fem"
   - Permet le groupement des sports côté frontend

4. **Exclusions**
   - Matchs avec forfait (`forfait_1=True` ou `forfait_2=True`)
   - Niveaux vides ou null

### Tri

Les niveaux sont triés par ordre alphabétique/numérique.

---

## 💡 Cas d'Usage Frontend

### Workflow Typique

1. **Utilisateur sélectionne une académie** : "Paris"
   - Aucun appel API (liste hardcodée ou depuis `/api/academies/available/`)

2. **Utilisateur sélectionne un sport** : "Football"
   - ✅ Appel API : `GET /api/available-levels/?academie=Paris&sport=Football`
   - Réponse : `{"levels": ["U15", "U17", "U19"], "count": 3}`
   - Frontend affiche 3 chips de niveau

3. **Utilisateur sélectionne un niveau** : "U17"
   - Appel API : `GET /api/matches/filtered/?academie=Paris&sport=Football&niveau=U17`
   - Affichage des matchs U17 uniquement

---

## 📊 Exemples de Requêtes

### Exemple 1 : Football à Paris

**Requête** :
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/available-levels/?academie=Paris&sport=Football"
```

**Réponse** :
```json
{
  "levels": ["U15", "U17", "U19", "Senior"],
  "count": 4
}
```

### Exemple 2 : Basketball à Toulouse

**Requête** :
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/available-levels/?academie=Toulouse&sport=Basketball"
```

**Réponse** :
```json
{
  "levels": ["U17", "Senior"],
  "count": 2
}
```

### Exemple 3 : Paramètres manquants (Erreur)

**Requête** :
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/available-levels/?academie=Paris"
```

**Réponse (400)** :
```json
{
  "error": "Les paramètres academie et sport sont requis"
}
```

---

## 🚀 Intégration Frontend

### Service API (TypeScript)

```typescript
// src/services/api.service.ts

interface LevelsResponse {
  levels: string[];
  count: number;
}

export class ApiService {
  async getAvailableLevels(
    academie: string,
    sport: string
  ): Promise<LevelsResponse> {
    const token = await this.storage.get('token');

    const response = await this.http.get(
      `${this.baseUrl}/api/available-levels/`,
      {
        academie: academie,
        sport: sport
      },
      {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    );

    return JSON.parse(response.data);
  }
}
```

### Utilisation dans Tab1.tsx

```typescript
// Tab1.tsx

const [availableLevels, setAvailableLevels] = useState<string[]>([]);

// Charger les niveaux quand académie ou sport change
useEffect(() => {
  if (selectedAcademie && selectedSport &&
      selectedAcademie !== 'all' && selectedSport !== 'all') {
    loadAvailableLevels();
  } else {
    setAvailableLevels([]);
    setSelectedNiveau('all');
  }
}, [selectedAcademie, selectedSport]);

const loadAvailableLevels = async () => {
  try {
    const response = await apiService.getAvailableLevels(
      selectedAcademie,
      selectedSport
    );

    setAvailableLevels(response.levels);

    console.log(`${response.count} niveaux disponibles`);

  } catch (error) {
    console.error('Erreur chargement niveaux:', error);
    setAvailableLevels([]);
  }
};
```

### UI - Affichage des Niveaux

```tsx
{/* Chips de niveaux */}
<IonChip
  color={selectedNiveau === 'all' ? 'primary' : 'medium'}
  onClick={() => setSelectedNiveau('all')}
>
  <IonLabel>Tous</IonLabel>
</IonChip>

{availableLevels.map((niveau) => (
  <IonChip
    key={niveau}
    color={selectedNiveau === niveau ? 'primary' : 'medium'}
    onClick={() => setSelectedNiveau(niveau)}
  >
    <IonLabel>{niveau}</IonLabel>
  </IonChip>
))}
```

---

## ⚡ Performance

### Optimisations

1. **Filtrage serveur** : Requête SQL optimisée
2. **Tri en DB** : `order_by('niveau')`
3. **Exclusion des niveaux vides** : Filtre Python léger

### Charge

- **Fréquence** : Faible (uniquement quand l'utilisateur change académie ou sport)
- **Payload** : Très léger (liste de quelques niveaux)
- **Temps de réponse** : < 100ms

### Cache (optionnel)

Si nécessaire, ajouter un cache Redis :

```python
from django.core.cache import cache

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_levels(request):
    academie = request.GET.get('academie')
    sport = request.GET.get('sport')

    # Clé de cache
    cache_key = f"levels_{academie}_{sport}"

    # Vérifier le cache
    cached_levels = cache.get(cache_key)
    if cached_levels:
        return Response({
            'levels': cached_levels,
            'count': len(cached_levels),
            'cached': True
        })

    # ... reste du code ...

    # Mettre en cache (5 minutes)
    cache.set(cache_key, list(levels), 300)

    return Response({
        'levels': list(levels),
        'count': len(levels)
    })
```

---

## 🧪 Tests

### Test Unitaire (à ajouter)

```python
# tests/test_views.py

from django.test import TestCase
from rest_framework.test import APIClient
from listings.models import Match

class AvailableLevelsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Créer des matchs de test
        Match.objects.create(
            academie="Paris",
            sport="Football Masc",
            niveau="U17",
            # ... autres champs
        )

    def test_available_levels_success(self):
        response = self.client.get(
            '/api/available-levels/',
            {'academie': 'Paris', 'sport': 'Football'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('levels', response.data)

    def test_available_levels_missing_params(self):
        response = self.client.get('/api/available-levels/')
        self.assertEqual(response.status_code, 400)
```

### Test Manuel

```bash
# Test avec curl
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://test.campus-league.com/api/available-levels/?academie=Paris&sport=Football" | jq
```

---

## 📝 Notes Importantes

### 1. Groupement des Sports

Le frontend peut grouper plusieurs variantes d'un sport :
- "Football Masc" + "Football Fem" → "Football"
- "Basketball Masc" + "Basketball Fem" → "Basketball"

L'endpoint utilise `icontains` pour matcher toutes les variantes.

### 2. Timezone

Les matchs futurs sont filtrés selon le timezone **Europe/Paris**.

### 3. Forfaits

Les matchs avec forfait sont **exclus** des niveaux disponibles.

### 4. Niveaux Vides

Les niveaux null ou vides sont **filtrés** de la réponse.

---

## 🔗 Endpoints Liés

| Endpoint | Description |
|----------|-------------|
| `/api/academies/available/` | Liste des académies |
| `/api/sports/available/` | Liste des sports |
| `/api/available-levels/` | ✨ **NOUVEAU** - Niveaux pour académie + sport |
| `/api/matches/filtered/` | Matchs filtrés (avec pagination) |
| `/api/sports/with-levels/` | Sports avec tous leurs niveaux |

---

## ✅ Checklist de Déploiement

- [x] Fonction `available_levels()` créée dans `views.py`
- [x] Route ajoutée dans `urls.py`
- [x] Syntaxe Python vérifiée
- [ ] Tester en local
- [ ] Déployer sur serveur TEST
- [ ] Tester depuis le frontend
- [ ] Valider les performances
- [ ] Déployer en PRODUCTION

---

## 📞 Support

En cas de problème :
1. Vérifier les logs : `tail -f /tmp/gunicorn-test-error.log`
2. Tester l'endpoint avec curl
3. Vérifier que les paramètres sont bien envoyés
4. Vérifier l'authentification JWT
