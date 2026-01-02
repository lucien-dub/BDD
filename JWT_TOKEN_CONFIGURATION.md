# 🔐 Configuration des Tokens JWT - Durée de Vie Étendue

## 📋 Objectif

Augmenter la durée de vie des tokens JWT pour améliorer l'expérience utilisateur en réduisant la fréquence de reconnexion.

---

## ⏱️ Nouvelle Configuration

### Durée de Vie des Tokens

| Token | Avant | Après | Impact |
|-------|-------|-------|--------|
| **Access Token** | 1 jour | **7 jours** | Connexion valide 1 semaine |
| **Refresh Token** | 1 jour (défaut) | **30 jours** | Renouvellement possible pendant 30 jours |

### Configuration Django (settings.py)

```python
SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),  # Token de connexion valide 7 jours
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Token de renouvellement valide 30 jours
    'ROTATE_REFRESH_TOKENS': True,  # Génère un nouveau refresh token à chaque renouvellement
}
```

---

## 🎯 Fonctionnement

### 1. Connexion Initiale

```
Utilisateur se connecte
    ↓
Backend génère 2 tokens:
    - Access Token (valide 7 jours)
    - Refresh Token (valide 30 jours)
    ↓
Frontend stocke les 2 tokens
```

### 2. Utilisation Normale (Jours 1-7)

```
Frontend envoie Access Token avec chaque requête
    ↓
Backend vérifie le token
    ↓
Si valide: Réponse OK
Si expiré: Erreur 401
```

### 3. Renouvellement (Après 7 jours)

```
Access Token expiré (après 7 jours)
    ↓
Frontend détecte erreur 401
    ↓
Frontend envoie Refresh Token à /api/token/refresh/
    ↓
Backend vérifie Refresh Token (valide 30 jours)
    ↓
Si valide:
    - Nouveau Access Token (7 jours)
    - Nouveau Refresh Token (30 jours) [rotation activée]
    ↓
Frontend stocke les nouveaux tokens
```

### 4. Reconnexion Requise (Après 30 jours)

```
Refresh Token expiré (après 30 jours)
    ↓
Frontend tente de renouveler
    ↓
Backend refuse (token expiré)
    ↓
Utilisateur doit se reconnecter
```

---

## ✨ Avantages

### Pour l'Utilisateur

1. **Moins de reconnexions** : Connexion valide 7 jours
2. **Session étendue** : Jusqu'à 30 jours sans reconnexion (avec renouvellement automatique)
3. **Meilleure UX** : Moins d'interruptions

### Pour le Système

1. **Rotation des tokens** : Sécurité améliorée
2. **Contrôle de session** : Expiration après 30 jours maximum
3. **Moins de charge** : Moins de requêtes de connexion

---

## 🔒 Sécurité

### Mesures de Sécurité Maintenues

1. **Expiration automatique** : Tokens expirent après la durée définie
2. **Rotation des refresh tokens** : Nouveau token à chaque renouvellement
3. **HTTPS obligatoire** : Transmission sécurisée des tokens
4. **Storage sécurisé** : Tokens stockés de manière sécurisée (localStorage ou sessionStorage avec précautions)

### Recommandations Supplémentaires

Pour une sécurité optimale en production :

1. **Activer la blacklist** (optionnel) :
   ```python
   # Dans settings.py - INSTALLED_APPS
   'rest_framework_simplejwt.token_blacklist',

   # Dans SIMPLE_JWT
   'BLACKLIST_AFTER_ROTATION': True,
   ```

2. **Forcer la reconnexion sur changement de mot de passe** :
   - Invalider tous les tokens existants
   - Demander une nouvelle connexion

3. **Surveiller les tentatives de renouvellement** :
   - Logger les renouvellements
   - Détecter les patterns suspects

---

## 🔄 Migration Frontend

### Avant

```typescript
// Token expiré après 1 jour
// Utilisateur doit se reconnecter tous les jours
```

### Après

```typescript
// Token valide 7 jours
// Renouvellement automatique jusqu'à 30 jours

// Exemple de service de renouvellement automatique
async function refreshTokenIfNeeded() {
  const accessToken = await storage.get('access_token');
  const refreshToken = await storage.get('refresh_token');

  try {
    // Essayer d'utiliser l'access token
    await apiCall(accessToken);
  } catch (error) {
    if (error.status === 401) {
      // Token expiré, tenter de renouveler
      try {
        const response = await http.post('/api/token/refresh/', {
          refresh: refreshToken
        });

        // Stocker les nouveaux tokens
        await storage.set('access_token', response.access);
        await storage.set('refresh_token', response.refresh);

        // Réessayer la requête initiale
        return await apiCall(response.access);
      } catch (refreshError) {
        // Refresh token expiré, rediriger vers login
        router.navigate('/login');
      }
    }
  }
}
```

---

## 📊 Scénarios d'Usage

### Scénario 1 : Utilisateur Actif Quotidien

```
Jour 1  : Connexion → Access Token valide 7 jours
Jour 2-7: Utilise Access Token (pas de renouvellement)
Jour 8  : Access Token expire → Renouvellement automatique
Jour 9-14: Utilise nouveau Access Token
...
Jour 30 : Refresh Token expire → Reconnexion requise
```

**Résultat** : 1 seule reconnexion en 30 jours

### Scénario 2 : Utilisateur Occasionnel

```
Jour 1  : Connexion → Tokens générés
Jour 5  : Utilise l'app → Access Token valide
Jour 15 : Ouvre l'app → Access Token expiré
        → Renouvellement automatique réussi
        → Continue à utiliser l'app
Jour 35 : Ouvre l'app → Refresh Token expiré
        → Reconnexion requise
```

**Résultat** : Reconnexion seulement après 30 jours d'inactivité

### Scénario 3 : Utilisateur Inactif > 30 jours

```
Jour 1  : Connexion
Jour 35 : Ouvre l'app
        → Refresh Token expiré
        → Reconnexion requise
```

**Résultat** : Sécurité maintenue avec expiration forcée

---

## 🧪 Tests

### Test 1 : Vérifier la durée de l'Access Token

```bash
# 1. Se connecter
curl -X POST https://test.campus-league.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test123"}'

# Réponse contient:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# 2. Décoder le token (jwt.io ou commande)
echo "eyJ0eXAiOiJKV1QiLCJhbGc..." | base64 -d

# 3. Vérifier "exp" (expiration timestamp)
# Doit être ~7 jours dans le futur
```

### Test 2 : Vérifier le renouvellement

```bash
# Attendre que l'access token expire (ou modifier manuellement)
# Puis tenter de renouveler

curl -X POST https://test.campus-league.com/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "REFRESH_TOKEN"}'

# Doit retourner de nouveaux tokens
```

---

## 📝 Impact sur l'Utilisation

### Backend

- ✅ Aucune modification de code nécessaire
- ✅ Changement de configuration uniquement
- ✅ Compatible avec le code existant

### Frontend

- 🔄 Implémentation du renouvellement automatique recommandée
- 🔄 Gestion de l'expiration du refresh token
- ✅ Code de connexion existant fonctionne sans modification

---

## 🚀 Déploiement

### Étapes

1. **Déployer sur TEST** :
   ```bash
   ssh ubuntu@test.campus-league.com
   cd /home/ubuntu/BDD-test
   git pull origin claude/add-decimal-import-9S6bC
   sudo ./restart-and-diagnostic.sh
   ```

2. **Tester** :
   - Se connecter depuis le frontend
   - Vérifier que le token dure bien 7 jours
   - Tester le renouvellement après 7 jours

3. **Déployer en PRODUCTION** :
   ```bash
   ssh ubuntu@campus-league.com
   cd /home/ubuntu/BDD
   git pull origin main  # Après merge de la branche
   sudo systemctl restart gunicorn
   ```

### Rollback (si nécessaire)

Si problème, revenir à la configuration précédente :

```python
SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Retour à 1 jour
}
```

---

## ⚠️ Notes Importantes

1. **Stockage Frontend** :
   - Utiliser `Ionic Storage` (chiffré)
   - Éviter `localStorage` en clair si possible
   - Nettoyer les tokens à la déconnexion

2. **Sécurité** :
   - HTTPS obligatoire en production
   - Ne jamais logger les tokens complets
   - Implémenter le renouvellement automatique côté frontend

3. **Compatibilité** :
   - Les utilisateurs déjà connectés devront se reconnecter après le déploiement
   - Les anciens tokens (1 jour) expireront normalement

4. **Monitoring** :
   - Surveiller les logs de renouvellement
   - Détecter les patterns suspects (renouvellements trop fréquents)

---

## 📞 Support

En cas de problème :

1. Vérifier les logs : `tail -f /tmp/gunicorn-test-error.log`
2. Vérifier la configuration : Chercher `SIMPLE_JWT` dans `settings.py`
3. Tester le renouvellement : `curl -X POST /api/token/refresh/`
4. Vérifier l'expiration du token avec jwt.io

---

## ✅ Checklist de Validation

- [x] Configuration modifiée dans `settings.py`
- [x] Syntaxe Python vérifiée
- [ ] Déployé sur serveur TEST
- [ ] Testé la connexion avec nouveau token
- [ ] Testé le renouvellement après 7 jours
- [ ] Validé l'expiration après 30 jours
- [ ] Frontend mis à jour avec renouvellement automatique
- [ ] Déployé en PRODUCTION
- [ ] Documentation mise à jour
