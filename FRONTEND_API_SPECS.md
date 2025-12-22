# Spécifications API pour le Frontend

## 🔐 Authentification

**Tous les endpoints requièrent une authentification JWT.**

Headers requis pour toutes les requêtes :
```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

---

## 📍 Endpoints Disponibles

### 1. `/api/all-users-bets/` - Tous les paris des utilisateurs

**Méthode** : `GET`
**URL** : `https://test.campus-league.com/api/all-users-bets/`
**Usage** : Récupérer tous les paris de tous les utilisateurs pour le leaderboard hebdomadaire

#### Paramètres de requête
Aucun paramètre requis

#### Format de réponse

```json
[
  {
    "user_id": 123,
    "username": "john.doe",
    "bets": [
      {
        "bet_id": 456,
        "paris": [
          {
            "pari_id": 789,
            "match": {
              "match_id": 101,
              "equipe1": "PSG",
              "equipe2": "OM",
              "date": "2024-01-15",
              "heure": "21:00:00",
              "academie": "Ile-de-France",
              "sport": "Football",
              "score1": 2,
              "score2": 1,
              "match_joue": true
            },
            "score1_parie": 2,
            "score2_parie": 1,
            "points": 5
          }
        ]
      }
    ]
  }
]
```

#### Exemple d'utilisation React

```javascript
const fetchAllUsersBets = async () => {
  try {
    const response = await fetch(
      'https://test.campus-league.com/api/all-users-bets/',
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) throw new Error('Erreur lors de la récupération');

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erreur:', error);
  }
};
```

---

### 2. `/api/available-academies/` - Liste des académies disponibles

**Méthode** : `GET`
**URL** : `https://test.campus-league.com/api/available-academies/`
**Usage** : Récupérer la liste des académies ayant des matchs à venir (pour filtrage)

⚠️ **IMPORTANT** : L'endpoint a été renommé de `/api/academies/available/` vers `/api/available-academies/` pour éviter les conflits de routing

#### Paramètres de requête
Aucun

#### Format de réponse

```json
{
  "academies": [
    "Ile-de-France",
    "Auvergne-Rhône-Alpes",
    "Provence-Alpes-Côte d'Azur",
    "Nouvelle-Aquitaine"
  ],
  "count": 4
}
```

#### Exemple d'utilisation React

```javascript
const fetchAvailableAcademies = async () => {
  try {
    const response = await fetch(
      'https://test.campus-league.com/api/available-academies/',
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    return data.academies;
  } catch (error) {
    console.error('Erreur:', error);
  }
};

// Utilisation dans un composant
const [academies, setAcademies] = useState([]);

useEffect(() => {
  fetchAvailableAcademies().then(data => {
    setAcademies(['all', ...data]); // Ajouter 'all' pour option "Toutes"
  });
}, []);
```

---

### 3. `/api/sports/available/` - Liste des sports disponibles

**Méthode** : `GET`
**URL** : `https://test.campus-league.com/api/sports/available/`
**Usage** : Récupérer la liste des sports ayant des matchs à venir (pour filtrage)

#### Paramètres de requête
Aucun

#### Format de réponse

```json
{
  "sports": [
    "Football",
    "Basketball",
    "Handball",
    "Rugby",
    "Volleyball"
  ],
  "count": 5
}
```

#### Exemple d'utilisation React

```javascript
const fetchAvailableSports = async () => {
  try {
    const response = await fetch(
      'https://test.campus-league.com/api/sports/available/',
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    return data.sports;
  } catch (error) {
    console.error('Erreur:', error);
  }
};
```

---

### 4. `/api/matches/filtered/` - Matchs à venir (filtrés et paginés)

**Méthode** : `GET`
**URL** : `https://test.campus-league.com/api/matches/filtered/`
**Usage** : Récupérer les matchs à venir avec filtrage côté serveur et pagination

⚠️ **Filtrage strict** : Retourne uniquement les matchs avec `match_joue=False` ET sans scores (ou scores à 0)

#### Paramètres de requête

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `academie` | string | - | Nom de l'académie (ou "all" pour toutes) |
| `sport` | string | - | Nom du sport (ou "all" pour tous) |
| `niveau` | string | - | Niveau du match (ou "all" pour tous) |
| `page` | integer | 1 | Numéro de page |
| `page_size` | integer | 15 | Nombre de résultats par page |

#### Format de réponse

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
      "niveau": "Universitaire",
      "equipe1": "Team A",
      "equipe2": "Team B",
      "score1": null,
      "score2": null,
      "match_joue": false,
      "lieu": "Gymnase Central"
    }
  ]
}
```

#### Exemple d'utilisation React avec pagination et filtres

```javascript
const fetchFilteredMatches = async (filters = {}) => {
  const {
    academie = 'all',
    sport = 'all',
    niveau = 'all',
    page = 1,
    pageSize = 15
  } = filters;

  const params = new URLSearchParams({
    academie,
    sport,
    niveau,
    page: page.toString(),
    page_size: pageSize.toString()
  });

  try {
    const response = await fetch(
      `https://test.campus-league.com/api/matches/filtered/?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erreur:', error);
  }
};

// Exemple d'utilisation dans un composant avec état
const MatchesList = () => {
  const [matches, setMatches] = useState([]);
  const [pagination, setPagination] = useState({});
  const [filters, setFilters] = useState({
    academie: 'all',
    sport: 'all',
    niveau: 'all',
    page: 1,
    pageSize: 15
  });

  useEffect(() => {
    fetchFilteredMatches(filters).then(data => {
      setMatches(data.results);
      setPagination({
        count: data.count,
        page: data.page,
        totalPages: data.total_pages,
        hasNext: data.has_next,
        hasPrevious: data.has_previous
      });
    });
  }, [filters]);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value,
      page: 1 // Reset à la page 1 quand on change un filtre
    }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  return (
    <div>
      {/* Filtres */}
      <select onChange={(e) => handleFilterChange('academie', e.target.value)}>
        <option value="all">Toutes les académies</option>
        {/* ... autres options */}
      </select>

      {/* Liste des matchs */}
      {matches.map(match => (
        <div key={match.id}>{/* Affichage du match */}</div>
      ))}

      {/* Pagination */}
      <button
        disabled={!pagination.hasPrevious}
        onClick={() => handlePageChange(filters.page - 1)}
      >
        Précédent
      </button>
      <span>Page {pagination.page} / {pagination.totalPages}</span>
      <button
        disabled={!pagination.hasNext}
        onClick={() => handlePageChange(filters.page + 1)}
      >
        Suivant
      </button>
    </div>
  );
};
```

---

### 5. `/api/results/filtered/` - Résultats des matchs terminés (filtrés et paginés)

**Méthode** : `GET`
**URL** : `https://test.campus-league.com/api/results/filtered/`
**Usage** : Récupérer les résultats des matchs terminés avec filtrage côté serveur et pagination

⚠️ **Filtrage strict** : Retourne uniquement les matchs avec `match_joue=True` ET `score1` ET `score2` non null

#### Paramètres de requête

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `academie` | string | - | Nom de l'académie (ou "all" pour toutes) |
| `sport` | string | - | Nom du sport (ou "all" pour tous) |
| `page` | integer | 1 | Numéro de page |
| `page_size` | integer | 50 | Nombre de résultats par page |

#### Format de réponse

```json
{
  "count": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 123,
      "date": "2024-01-15",
      "heure": "14:00:00",
      "academie": "Ile-de-France",
      "sport": "Football",
      "niveau": "Universitaire",
      "equipe1": "Team A",
      "equipe2": "Team B",
      "score1": 2,
      "score2": 1,
      "match_joue": true,
      "lieu": "Stade Municipal"
    }
  ]
}
```

#### Exemple d'utilisation React avec infinite scroll

```javascript
const fetchFilteredResults = async (filters = {}) => {
  const {
    academie = 'all',
    sport = 'all',
    page = 1,
    pageSize = 50
  } = filters;

  const params = new URLSearchParams({
    academie,
    sport,
    page: page.toString(),
    page_size: pageSize.toString()
  });

  try {
    const response = await fetch(
      `https://test.campus-league.com/api/results/filtered/?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erreur:', error);
  }
};

// Exemple avec infinite scroll
const ResultsList = () => {
  const [results, setResults] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [filters, setFilters] = useState({
    academie: 'all',
    sport: 'all'
  });

  const loadMore = async () => {
    const data = await fetchFilteredResults({
      ...filters,
      page,
      pageSize: 50
    });

    setResults(prev => [...prev, ...data.results]);
    setHasMore(data.has_next);
    setPage(prev => prev + 1);
  };

  useEffect(() => {
    // Reset quand les filtres changent
    setResults([]);
    setPage(1);
    setHasMore(true);
    loadMore();
  }, [filters]);

  return (
    <div>
      {/* Filtres */}
      <select onChange={(e) => setFilters(prev => ({
        ...prev,
        academie: e.target.value
      }))}>
        <option value="all">Toutes les académies</option>
        {/* ... */}
      </select>

      {/* Liste des résultats */}
      {results.map(result => (
        <div key={result.id}>
          <div>{result.equipe1} {result.score1} - {result.score2} {result.equipe2}</div>
          <div>{result.date} {result.heure}</div>
        </div>
      ))}

      {/* Bouton charger plus */}
      {hasMore && (
        <button onClick={loadMore}>Charger plus</button>
      )}
    </div>
  );
};
```

---

## 🔄 Différences importantes avec l'ancien système

### 1. **Filtrage côté serveur**
- ✅ **Avant** : Récupération de tous les matchs puis filtrage côté frontend
- ✅ **Après** : Filtrage et pagination côté serveur → performance améliorée

### 2. **Endpoint académies renommé**
- ❌ **Ancien** : `/api/academies/available/` (404 error)
- ✅ **Nouveau** : `/api/available-academies/`

### 3. **Pagination ajoutée**
- `/api/results/filtered/` inclut maintenant la pagination complète
- Permet de charger les résultats progressivement (infinite scroll)

### 4. **Filtrage strict des matchs**
- **Matchs à venir** : Garantit que `match_joue=False` ET pas de scores
- **Matchs terminés** : Garantit que `match_joue=True` ET scores présents
- Plus de matchs mal catégorisés entre "à venir" et "terminés"

---

## 📝 Exemple de service API complet (React/TypeScript)

```typescript
// services/api.ts

const API_BASE_URL = 'https://test.campus-league.com';

// Types
interface Match {
  id: number;
  date: string;
  heure: string;
  academie: string;
  sport: string;
  niveau?: string;
  equipe1: string;
  equipe2: string;
  score1: number | null;
  score2: number | null;
  match_joue: boolean;
  lieu?: string;
}

interface PaginatedResponse<T> {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
  results: T[];
}

interface MatchFilters {
  academie?: string;
  sport?: string;
  niveau?: string;
  page?: number;
  pageSize?: number;
}

class ApiService {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  // Académies disponibles
  async getAvailableAcademies(): Promise<string[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/available-academies/`,
      { headers: this.getHeaders() }
    );

    if (!response.ok) throw new Error('Erreur récupération académies');

    const data = await response.json();
    return data.academies;
  }

  // Sports disponibles
  async getAvailableSports(): Promise<string[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/sports/available/`,
      { headers: this.getHeaders() }
    );

    if (!response.ok) throw new Error('Erreur récupération sports');

    const data = await response.json();
    return data.sports;
  }

  // Matchs à venir (filtrés et paginés)
  async getFilteredMatches(
    filters: MatchFilters = {}
  ): Promise<PaginatedResponse<Match>> {
    const params = new URLSearchParams({
      academie: filters.academie || 'all',
      sport: filters.sport || 'all',
      niveau: filters.niveau || 'all',
      page: (filters.page || 1).toString(),
      page_size: (filters.pageSize || 15).toString()
    });

    const response = await fetch(
      `${API_BASE_URL}/api/matches/filtered/?${params}`,
      { headers: this.getHeaders() }
    );

    if (!response.ok) throw new Error('Erreur récupération matchs');

    return await response.json();
  }

  // Résultats (matchs terminés)
  async getFilteredResults(
    filters: Omit<MatchFilters, 'niveau'> = {}
  ): Promise<PaginatedResponse<Match>> {
    const params = new URLSearchParams({
      academie: filters.academie || 'all',
      sport: filters.sport || 'all',
      page: (filters.page || 1).toString(),
      page_size: (filters.pageSize || 50).toString()
    });

    const response = await fetch(
      `${API_BASE_URL}/api/results/filtered/?${params}`,
      { headers: this.getHeaders() }
    );

    if (!response.ok) throw new Error('Erreur récupération résultats');

    return await response.json();
  }

  // Tous les paris des utilisateurs
  async getAllUsersBets(): Promise<any[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/all-users-bets/`,
      { headers: this.getHeaders() }
    );

    if (!response.ok) throw new Error('Erreur récupération paris');

    return await response.json();
  }
}

export const apiService = new ApiService();
```

---

## 🚨 Points d'attention pour le frontend

### 1. **Migration de l'URL académies**
Remplacer toutes les occurrences :
```javascript
// ❌ Ancien
fetch('/api/academies/available/')

// ✅ Nouveau
fetch('/api/available-academies/')
```

### 2. **Gestion de la pagination**
Ne plus charger tous les matchs d'un coup, utiliser la pagination :
```javascript
// ❌ Ancien (risque de timeout)
const allMatches = await fetch('/api/matches/');

// ✅ Nouveau (avec pagination)
const page1 = await fetch('/api/matches/filtered/?page=1&page_size=15');
```

### 3. **Filtres par défaut**
Toujours envoyer 'all' pour les filtres non utilisés :
```javascript
const params = {
  academie: selectedAcademie || 'all',
  sport: selectedSport || 'all'
};
```

### 4. **Gestion des erreurs d'authentification**
```javascript
const response = await fetch(url, { headers });

if (response.status === 401) {
  // Token expiré, rediriger vers login
  redirectToLogin();
  return;
}
```

### 5. **Cache et rafraîchissement**
Les listes d'académies et sports peuvent être cachées :
```javascript
// Charger une seule fois au montage de l'app
useEffect(() => {
  apiService.getAvailableAcademies().then(setAcademies);
  apiService.getAvailableSports().then(setSports);
}, []); // Dépendances vides
```

---

## 📊 Résumé des changements à faire

| Composant/Page | Action | Priorité |
|----------------|--------|----------|
| **Tab3.tsx** (Leaderboard) | Utiliser `/api/all-users-bets/` | 🔴 Haute |
| **Filtres académies** | Changer URL vers `/api/available-academies/` | 🔴 Haute |
| **Liste matchs** | Implémenter pagination avec `/api/matches/filtered/` | 🟡 Moyenne |
| **Résultats** | Implémenter pagination avec `/api/results/filtered/` | 🟡 Moyenne |
| **Service API** | Créer service centralisé | 🟢 Basse |

---

## ✅ Checklist d'intégration

- [ ] Créer le service API centralisé (`services/api.ts`)
- [ ] Migrer `/api/academies/available/` → `/api/available-academies/`
- [ ] Implémenter la pagination pour les matchs à venir
- [ ] Implémenter la pagination pour les résultats
- [ ] Intégrer `/api/all-users-bets/` dans Tab3.tsx
- [ ] Tester tous les endpoints avec authentification
- [ ] Gérer les erreurs 401 (token expiré)
- [ ] Ajouter un loader pendant le chargement des données
- [ ] Tester le filtrage par académie et sport
- [ ] Tester la pagination (navigation entre pages)
