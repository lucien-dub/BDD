# 🔄 Guide de Migration - Tab1.tsx pour les Nouveaux Endpoints

## 📋 Objectif

Mettre à jour Tab1.tsx pour utiliser les nouveaux endpoints backend :
- `/api/sports/with-levels/` : Pour récupérer les sports avec leurs niveaux
- `/api/matches/all-future/` : Pour récupérer tous les matchs futurs

---

## ✅ Avantages de la Migration

### Avant (ancien système)
- Appels multiples pour récupérer sports, niveaux et matchs séparément
- Filtrage côté client (lourd et lent)
- Données non synchronisées

### Après (nouveau système)
- **Un seul appel** pour récupérer sports + niveaux
- **Un seul appel** pour récupérer tous les matchs (avec filtres serveur)
- Filtrage côté serveur (rapide et efficace)
- Données toujours cohérentes

---

## 📝 Modifications à Apporter

### 1. **Mise à jour des Types TypeScript**

```typescript
// src/types/Match.types.ts (ou dans Tab1.tsx si pas de fichier séparé)

export interface SportWithLevels {
  sport: string;
  niveaux: string[];
}

export interface SportsResponse {
  sports: SportWithLevels[];
  count: number;
}

export interface MatchesResponse {
  matches: Match[];
  count: number;
  total_available: number;
  filters: {
    academie: string;
    sport: string;
    niveau: string;
  };
}
```

---

### 2. **Service API - Nouveaux Endpoints**

Ajouter dans votre fichier de services (ex: `src/services/api.service.ts`)

```typescript
// src/services/api.service.ts

import { HTTP } from '@ionic-native/http/ngx';
import { Storage } from '@ionic/storage-angular';

export class ApiService {
  private baseUrl = 'https://test.campus-league.com'; // ou campus-league.com en prod

  constructor(
    private http: HTTP,
    private storage: Storage
  ) {}

  /**
   * Récupère tous les sports disponibles avec leurs niveaux
   */
  async getSportsWithLevels(): Promise<SportsResponse> {
    const token = await this.storage.get('token');

    const response = await this.http.get(
      `${this.baseUrl}/api/sports/with-levels/`,
      {},
      {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    );

    return JSON.parse(response.data);
  }

  /**
   * Récupère tous les matchs futurs (avec filtres optionnels)
   */
  async getAllFutureMatches(
    filters?: {
      academie?: string;
      sport?: string;
      niveau?: string;
    }
  ): Promise<MatchesResponse> {
    const token = await this.storage.get('token');

    // Construire les query params
    const params: any = {};
    if (filters?.academie && filters.academie !== 'all') {
      params.academie = filters.academie;
    }
    if (filters?.sport && filters.sport !== 'all') {
      params.sport = filters.sport;
    }
    if (filters?.niveau && filters.niveau !== 'all') {
      params.niveau = filters.niveau;
    }

    const response = await this.http.get(
      `${this.baseUrl}/api/matches/all-future/`,
      params,
      {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    );

    return JSON.parse(response.data);
  }
}
```

---

### 3. **Modification de Tab1.tsx - State Management**

```typescript
// Tab1.tsx

import { useState, useEffect } from 'react';
import { ApiService } from '../services/api.service';

export const Tab1: React.FC = () => {
  // États
  const [sportsData, setSportsData] = useState<SportWithLevels[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);

  // Filtres sélectionnés
  const [selectedAcademie, setSelectedAcademie] = useState<string>('all');
  const [selectedSport, setSelectedSport] = useState<string>('all');
  const [selectedNiveau, setSelectedNiveau] = useState<string>('all');

  // Services
  const apiService = new ApiService(http, storage);

  // ... reste du code
}
```

---

### 4. **Chargement Initial - Sports et Niveaux**

```typescript
// Tab1.tsx

useEffect(() => {
  loadSportsWithLevels();
}, []);

/**
 * Charge les sports disponibles avec leurs niveaux
 */
const loadSportsWithLevels = async () => {
  try {
    setLoading(true);

    const response = await apiService.getSportsWithLevels();

    setSportsData(response.sports);

    console.log('Sports chargés:', response.sports);
    // Exemple de sortie :
    // [
    //   { sport: "Football", niveaux: ["Lycée", "Universitaire"] },
    //   { sport: "Basketball", niveaux: ["Post-Bac", "Universitaire"] }
    // ]

  } catch (error) {
    console.error('Erreur chargement sports:', error);
    // Afficher un toast d'erreur à l'utilisateur
  } finally {
    setLoading(false);
  }
};
```

---

### 5. **Chargement des Matchs avec Filtres**

```typescript
// Tab1.tsx

useEffect(() => {
  // Recharger les matchs quand les filtres changent
  loadMatches();
}, [selectedAcademie, selectedSport, selectedNiveau]);

/**
 * Charge tous les matchs futurs avec les filtres actifs
 */
const loadMatches = async () => {
  try {
    setLoading(true);

    const response = await apiService.getAllFutureMatches({
      academie: selectedAcademie,
      sport: selectedSport,
      niveau: selectedNiveau
    });

    setMatches(response.matches);

    console.log(`${response.count} matchs chargés sur ${response.total_available} disponibles`);

  } catch (error) {
    console.error('Erreur chargement matchs:', error);
    // Afficher un toast d'erreur
  } finally {
    setLoading(false);
  }
};
```

---

### 6. **UI - Select des Sports avec Niveaux**

```tsx
// Tab1.tsx - Rendu JSX

return (
  <IonPage>
    <IonHeader>
      <IonToolbar>
        <IonTitle>Matchs à Venir</IonTitle>
      </IonToolbar>
    </IonHeader>

    <IonContent>
      {/* Filtres */}
      <IonCard>
        <IonCardContent>
          {/* Filtre Académie */}
          <IonItem>
            <IonLabel>Académie</IonLabel>
            <IonSelect
              value={selectedAcademie}
              onIonChange={(e) => setSelectedAcademie(e.detail.value)}
            >
              <IonSelectOption value="all">Toutes</IonSelectOption>
              {/* Récupéré depuis un autre endpoint ou hardcodé */}
              <IonSelectOption value="Toulouse">Toulouse</IonSelectOption>
              <IonSelectOption value="Paris">Paris</IonSelectOption>
            </IonSelect>
          </IonItem>

          {/* Filtre Sport */}
          <IonItem>
            <IonLabel>Sport</IonLabel>
            <IonSelect
              value={selectedSport}
              onIonChange={(e) => {
                setSelectedSport(e.detail.value);
                // Réinitialiser le niveau quand on change de sport
                setSelectedNiveau('all');
              }}
            >
              <IonSelectOption value="all">Tous</IonSelectOption>
              {sportsData.map((sportData) => (
                <IonSelectOption key={sportData.sport} value={sportData.sport}>
                  {sportData.sport}
                </IonSelectOption>
              ))}
            </IonSelect>
          </IonItem>

          {/* Filtre Niveau (dynamique selon le sport sélectionné) */}
          <IonItem>
            <IonLabel>Niveau</IonLabel>
            <IonSelect
              value={selectedNiveau}
              onIonChange={(e) => setSelectedNiveau(e.detail.value)}
              disabled={selectedSport === 'all'}
            >
              <IonSelectOption value="all">Tous</IonSelectOption>
              {selectedSport !== 'all' &&
                sportsData
                  .find((s) => s.sport === selectedSport)
                  ?.niveaux.map((niveau) => (
                    <IonSelectOption key={niveau} value={niveau}>
                      {niveau}
                    </IonSelectOption>
                  ))}
            </IonSelect>
          </IonItem>

          {/* Indicateur de nombre de matchs */}
          <IonItem lines="none">
            <IonLabel color="medium">
              <small>{matches.length} match{matches.length > 1 ? 's' : ''} trouvé{matches.length > 1 ? 's' : ''}</small>
            </IonLabel>
          </IonItem>
        </IonCardContent>
      </IonCard>

      {/* Loader */}
      {loading && (
        <IonCard>
          <IonCardContent className="ion-text-center">
            <IonSpinner />
            <p>Chargement...</p>
          </IonCardContent>
        </IonCard>
      )}

      {/* Liste des matchs */}
      {!loading && matches.length === 0 && (
        <IonCard>
          <IonCardContent className="ion-text-center">
            <p>Aucun match à venir avec ces filtres</p>
          </IonCardContent>
        </IonCard>
      )}

      {!loading && matches.length > 0 && (
        <IonList>
          {matches.map((match) => (
            <IonCard key={match.id}>
              <IonCardHeader>
                <IonCardSubtitle>
                  {match.sport} - {match.niveau} - {match.academie}
                </IonCardSubtitle>
                <IonCardTitle>
                  {match.equipe1} vs {match.equipe2}
                </IonCardTitle>
              </IonCardHeader>
              <IonCardContent>
                <p>
                  📅 {new Date(match.date).toLocaleDateString('fr-FR')} à {match.heure}
                </p>
                {match.lieu && <p>📍 {match.lieu}</p>}

                {/* Bouton pour parier */}
                <IonButton
                  expand="block"
                  onClick={() => handleAddToBetCart(match)}
                >
                  Ajouter au panier
                </IonButton>
              </IonCardContent>
            </IonCard>
          ))}
        </IonList>
      )}
    </IonContent>
  </IonPage>
);
```

---

### 7. **Gestion d'Erreurs et Cache**

```typescript
// Tab1.tsx

// Cache pour éviter de recharger les sports à chaque fois
const [sportsCache, setSportsCache] = useState<SportWithLevels[] | null>(null);
const [sportsCacheTimestamp, setSportsCacheTimestamp] = useState<number>(0);

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Charge les sports avec cache
 */
const loadSportsWithLevels = async (forceRefresh = false) => {
  try {
    // Vérifier le cache
    const now = Date.now();
    if (!forceRefresh && sportsCache && (now - sportsCacheTimestamp < CACHE_DURATION)) {
      console.log('Utilisation du cache pour les sports');
      setSportsData(sportsCache);
      return;
    }

    setLoading(true);

    const response = await apiService.getSportsWithLevels();

    setSportsData(response.sports);
    setSportsCache(response.sports);
    setSportsCacheTimestamp(now);

  } catch (error: any) {
    console.error('Erreur chargement sports:', error);

    // Afficher un message utilisateur
    const toast = await toastController.create({
      message: 'Erreur lors du chargement des sports',
      duration: 3000,
      color: 'danger',
      position: 'top'
    });
    await toast.present();

    // Utiliser le cache si disponible en cas d'erreur réseau
    if (sportsCache) {
      setSportsData(sportsCache);
    }

  } finally {
    setLoading(false);
  }
};
```

---

## 🔄 Migration Progressive (Option)

Si tu ne veux pas tout migrer d'un coup, tu peux faire une migration progressive :

### Étape 1 : Migrer uniquement le chargement des sports

```typescript
// Garder l'ancien système pour les matchs
const [matches, setMatches] = useState([]);

// Nouveau système pour les sports
const [sportsData, setSportsData] = useState<SportWithLevels[]>([]);

useEffect(() => {
  loadSportsWithLevels(); // Nouveau
  loadMatchesOldWay(); // Ancien système conservé temporairement
}, []);
```

### Étape 2 : Migrer le chargement des matchs

Une fois que le chargement des sports fonctionne, migrer ensuite les matchs.

---

## ✅ Checklist de Migration

- [ ] Créer/mettre à jour les types TypeScript
- [ ] Ajouter les nouvelles fonctions dans le service API
- [ ] Mettre à jour le state management dans Tab1
- [ ] Implémenter `loadSportsWithLevels()`
- [ ] Implémenter `loadMatches()` avec filtres
- [ ] Mettre à jour l'UI des filtres (select sports/niveaux)
- [ ] Tester le chargement initial
- [ ] Tester le changement de filtres
- [ ] Ajouter la gestion d'erreurs
- [ ] Ajouter le cache (optionnel mais recommandé)
- [ ] Tester avec des données réelles du serveur
- [ ] Supprimer l'ancien code une fois la migration validée

---

## 🧪 Tests à Effectuer

1. **Test de chargement initial**
   - Vérifier que les sports et niveaux se chargent
   - Vérifier que les matchs s'affichent

2. **Test des filtres**
   - Sélectionner un sport → vérifier que seuls ses niveaux s'affichent
   - Sélectionner un niveau → vérifier que les matchs sont filtrés
   - Changer d'académie → vérifier le filtrage

3. **Test de performance**
   - Comparer le temps de chargement avant/après
   - Vérifier que le cache fonctionne

4. **Test d'erreurs**
   - Tester sans connexion internet
   - Tester avec un token expiré
   - Vérifier les messages d'erreur

---

## 📊 Comparaison Avant/Après

| Critère | Avant | Après |
|---------|-------|-------|
| **Appels API** | 3-4 appels | 2 appels |
| **Temps de chargement** | 2-3s | < 1s |
| **Filtrage** | Côté client | Côté serveur |
| **Maintenance** | Complexe | Simple |
| **Cohérence données** | Risque de désync | Toujours cohérent |

---

## 🚀 Déploiement

Une fois les modifications faites :

1. **Tester en local** contre `test.campus-league.com`
2. **Valider** que tout fonctionne
3. **Commiter** les changements
4. **Déployer** le frontend
5. **Surveiller** les logs pour détecter d'éventuels problèmes

---

## ❓ Questions Fréquentes

**Q: Que faire si l'API retourne une erreur 401 ?**
R: Le token JWT a expiré. Rediriger vers la page de login.

**Q: Les niveaux ne s'affichent pas pour un sport ?**
R: Vérifier que `selectedSport !== 'all'` et que le sport existe dans `sportsData`.

**Q: Les matchs ne se rechargent pas quand je change de filtre ?**
R: Vérifier que le `useEffect` a bien les bonnes dépendances : `[selectedAcademie, selectedSport, selectedNiveau]`.

**Q: Le chargement est trop lent ?**
R: Implémenter le cache et vérifier la connexion réseau.

---

## 📞 Support

Si tu rencontres des problèmes :
1. Vérifier les logs dans la console du navigateur
2. Vérifier les logs du serveur backend
3. Tester les endpoints directement avec curl
4. Me poser des questions ! 😊
