# Guide du Système de Notifications Push - Campus League

## Vue d'ensemble

Ce système permet d'envoyer des notifications push aux utilisateurs lorsque leurs paris sont terminés (gagnés, perdus ou remboursés).

## Architecture

### 1. Firebase Cloud Messaging (FCM)

Le système utilise **Firebase Cloud Messaging (FCM)** comme service de notifications push. FCM est:
- ✅ Gratuit et fiable
- ✅ Compatible avec iOS, Android et Web
- ✅ Maintenu par Google
- ✅ Scalable et performant

### 2. Composants du Système

#### A. Modèles de Base de Données (`listings/models.py`)

**FCMDevice** - Stocke les tokens des appareils utilisateurs
```python
class FCMDevice(models.Model):
    user = models.ForeignKey(User)              # Utilisateur propriétaire
    registration_id = models.CharField()        # Token FCM unique
    device_type = models.CharField()            # ios/android/web
    device_name = models.CharField()            # Nom de l'appareil
    active = models.BooleanField()              # Statut actif/inactif
    date_created = models.DateTimeField()       # Date d'enregistrement
    last_used = models.DateTimeField()          # Dernière utilisation
```

**PushNotification** - Historique des notifications envoyées
```python
class PushNotification(models.Model):
    user = models.ForeignKey(User)              # Destinataire
    notification_type = models.CharField()      # bet_won/bet_lost/bet_refunded
    title = models.CharField()                  # Titre
    message = models.TextField()                # Message
    data = models.JSONField()                   # Données additionnelles
    status = models.CharField()                 # pending/sent/failed
    sent_at = models.DateTimeField()           # Date d'envoi
    error_message = models.TextField()          # Erreur éventuelle
```

#### B. Service de Notifications (`listings/push_notifications.py`)

**PushNotificationService** - Gère l'envoi des notifications

Méthodes principales:
- `send_notification()` - Envoi générique
- `send_bet_won_notification()` - Paris gagnés
- `send_bet_lost_notification()` - Paris perdus
- `send_bet_refunded_notification()` - Paris remboursés
- `send_daily_bonus_notification()` - Bonus quotidien

#### C. Endpoints API (`listings/views.py`)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/fcm/register/` | POST | Enregistrer un token FCM |
| `/api/fcm/unregister/` | POST | Supprimer un token FCM |
| `/api/fcm/devices/` | GET | Lister les appareils de l'utilisateur |
| `/api/fcm/test/` | POST | Tester l'envoi de notifications |
| `/api/notifications/history/` | GET | Historique des notifications |

#### D. Intégration dans la Logique Métier (`listings/models.py`)

La méthode `Bet.verifier_statut()` a été modifiée pour envoyer automatiquement des notifications:

```python
def verifier_statut(self):
    # ... logique de vérification ...

    # Pari gagné
    if tous_paris_gagnes and paris_verifies:
        # Attribution des points
        notification_service.send_bet_won_notification(self)

    # Pari perdu
    elif pari_perdu:
        notification_service.send_bet_lost_notification(self)

    # Match annulé
    elif match_annule:
        notification_service.send_bet_refunded_notification(self)
```

## Flux de Fonctionnement

### 1. Enregistrement d'un Appareil

```
┌─────────────┐      POST /api/fcm/register/      ┌─────────────┐
│   Client    │─────────────────────────────────>│   Backend   │
│ (iOS/Web)   │    {registration_id, device_type} │   Django    │
└─────────────┘                                    └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  FCMDevice  │
                                                   │   (BDD)     │
                                                   └─────────────┘
```

**Exemple de requête:**
```json
POST /api/fcm/register/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "registration_id": "eXaMpLeToKeN123456789...",
    "device_type": "web",
    "device_name": "Chrome sur MacBook Pro"
}
```

### 2. Vérification des Paris (Automatique)

```
┌──────────────┐      Score Update       ┌──────────────┐
│    Match     │────────────────────────>│ Match.save() │
└──────────────┘                          └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ Bet.verifier │
                                          │  _statut()   │
                                          └──────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    ▼                             ▼                             ▼
            ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
            │ Pari Gagné    │           │ Pari Perdu    │           │ Pari Remb.    │
            └───────────────┘           └───────────────┘           └───────────────┘
                    │                             │                             │
                    ▼                             ▼                             ▼
         ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
         │ Notification FCM │        │ Notification FCM │        │ Notification FCM │
         │    "🎉 Gagné!"   │        │    "❌ Perdu"    │        │   "💰 Remb."     │
         └──────────────────┘        └──────────────────┘        └──────────────────┘
                    │                             │                             │
                    └─────────────────────────────┴─────────────────────────────┘
                                                  │
                                                  ▼
                                        ┌───────────────────┐
                                        │  PushNotification │
                                        │    (Historique)   │
                                        └───────────────────┘
```

### 3. Envoi de la Notification

```
┌─────────────┐     send_notification()    ┌─────────────┐
│  Bet Model  │──────────────────────────>│   Service   │
└─────────────┘                            │     FCM     │
                                           └─────────────┘
                                                   │
                                                   ▼
                                           Récupère tokens
                                           actifs de l'user
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │ Firebase    │
                                           │ Cloud       │
                                           │ Messaging   │
                                           └─────────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                            ┌──────────┐   ┌──────────┐   ┌──────────┐
                            │ iPhone   │   │ Android  │   │   Web    │
                            └──────────┘   └──────────┘   └──────────┘
```

## Configuration Requise

### 1. Créer un Projet Firebase

1. Allez sur https://console.firebase.google.com/
2. Créez un nouveau projet "Campus League"
3. Activez **Cloud Messaging** dans les paramètres du projet
4. Récupérez la **Clé du serveur** (Server Key)

### 2. Configurer Django

Dans `/home/user/BDD/merchex/merchex/settings.py`:

```python
# Configuration Firebase Cloud Messaging (FCM)
FCM_SERVER_KEY = os.environ.get('FCM_SERVER_KEY', 'VOTRE_CLE_SERVEUR_FCM_ICI')
```

**Méthode recommandée:** Utiliser une variable d'environnement:
```bash
export FCM_SERVER_KEY="AAAA...votre_cle_serveur_fcm"
```

### 3. Installer les Dépendances

```bash
pip install fcm-django==2.0.0 pyfcm==1.5.4
```

### 4. Créer et Appliquer les Migrations

```bash
cd /home/user/BDD/merchex
python manage.py makemigrations
python manage.py migrate
```

## Intégration Client

### Web (JavaScript)

#### 1. Initialiser Firebase dans votre application web

```javascript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  projectId: "campus-league",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);
```

#### 2. Demander la permission et récupérer le token

```javascript
async function registerForPushNotifications() {
  try {
    // Demander la permission
    const permission = await Notification.requestPermission();

    if (permission === 'granted') {
      // Récupérer le token FCM
      const token = await getToken(messaging, {
        vapidKey: 'YOUR_VAPID_KEY'
      });

      // Envoyer le token au backend
      await fetch('https://campus-league.com/api/fcm/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${jwtToken}`
        },
        body: JSON.stringify({
          registration_id: token,
          device_type: 'web',
          device_name: navigator.userAgent
        })
      });

      console.log('Notifications activées !');
    }
  } catch (error) {
    console.error('Erreur:', error);
  }
}
```

#### 3. Écouter les notifications en arrière-plan

Créer `firebase-messaging-sw.js` dans le dossier public:

```javascript
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  projectId: "campus-league",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('Notification reçue:', payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/logo.png',
    badge: '/badge.png',
    data: payload.data
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
```

### iOS (Swift)

```swift
import Firebase
import FirebaseMessaging

// Dans AppDelegate
func application(_ application: UIApplication,
                 didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    FirebaseApp.configure()

    // Demander la permission
    UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
        if granted {
            DispatchQueue.main.async {
                application.registerForRemoteNotifications()
            }
        }
    }

    return true
}

// Récupérer le token FCM
func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
    guard let token = fcmToken else { return }

    // Envoyer au backend
    let url = URL(string: "https://campus-league.com/api/fcm/register/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")

    let body = [
        "registration_id": token,
        "device_type": "ios",
        "device_name": UIDevice.current.name
    ]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)

    URLSession.shared.dataTask(with: request).resume()
}
```

### Android (Kotlin)

```kotlin
import com.google.firebase.messaging.FirebaseMessaging

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Récupérer le token FCM
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val token = task.result
                registerTokenWithBackend(token)
            }
        }
    }

    private fun registerTokenWithBackend(token: String) {
        val url = "https://campus-league.com/api/fcm/register/"
        val json = JSONObject().apply {
            put("registration_id", token)
            put("device_type", "android")
            put("device_name", Build.MODEL)
        }

        val request = Request.Builder()
            .url(url)
            .post(json.toString().toRequestBody("application/json".toMediaType()))
            .addHeader("Authorization", "Bearer $jwtToken")
            .build()

        OkHttpClient().newCall(request).enqueue(...)
    }
}
```

## Types de Notifications

### 1. Pari Gagné
```json
{
    "title": "🎉 Pari gagné !",
    "message": "Félicitations ! Vous avez gagné 250 points avec votre pari (cote 2.5x)",
    "data": {
        "notification_type": "bet_won",
        "bet_id": 123,
        "gains": 250,
        "cote": 2.5,
        "mise": 100
    }
}
```

### 2. Pari Perdu
```json
{
    "title": "❌ Pari perdu",
    "message": "Votre pari de 100 points n'a pas été gagnant. Tentez votre chance à nouveau !",
    "data": {
        "notification_type": "bet_lost",
        "bet_id": 123,
        "mise": 100,
        "cote": 2.5
    }
}
```

### 3. Pari Remboursé
```json
{
    "title": "💰 Pari remboursé",
    "message": "Votre pari de 100 points a été remboursé suite à l'annulation d'un match.",
    "data": {
        "notification_type": "bet_refunded",
        "bet_id": 123,
        "mise": 100
    }
}
```

## Tests

### Tester l'Envoi de Notifications

```bash
# Enregistrer un token (exemple)
curl -X POST https://campus-league.com/api/fcm/register/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "registration_id": "eXaMpLeToKeN123...",
    "device_type": "web"
  }'

# Envoyer une notification de test
curl -X POST https://campus-league.com/api/fcm/test/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Voir l'historique des notifications
curl https://campus-league.com/api/notifications/history/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Sécurité et Bonnes Pratiques

### 1. Protection de la Clé Serveur
- ❌ **Ne jamais** commit la clé serveur dans Git
- ✅ Utiliser des variables d'environnement
- ✅ Utiliser des secrets managers en production (AWS Secrets Manager, etc.)

### 2. Validation des Tokens
- Les tokens invalides sont automatiquement désactivés
- Le système gère les erreurs FCM gracieusement

### 3. Gestion des Erreurs
- Toutes les erreurs sont loggées dans `/home/ubuntu/BDD/merchex/logs/django.log`
- Les notifications échouées sont enregistrées avec `status='failed'`

### 4. Performance
- Les notifications sont envoyées de manière asynchrone
- Pas de blocage de la logique métier
- Utilisation de `try/except` pour éviter les crashs

## Monitoring et Débogage

### Logs

Les logs sont enregistrés dans:
```
/home/ubuntu/BDD/merchex/logs/django.log
```

### Vérifier l'Historique

```sql
SELECT * FROM listings_pushnotification
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 10;
```

### Statistiques

```python
from listings.models import PushNotification

# Taux de succès
total = PushNotification.objects.count()
success = PushNotification.objects.filter(status='sent').count()
success_rate = (success / total) * 100 if total > 0 else 0

print(f"Taux de succès: {success_rate:.2f}%")
```

## Maintenance

### Nettoyer les Appareils Inactifs

```python
from listings.models import FCMDevice
from django.utils import timezone
from datetime import timedelta

# Désactiver les appareils non utilisés depuis 90 jours
cutoff_date = timezone.now() - timedelta(days=90)
FCMDevice.objects.filter(last_used__lt=cutoff_date).update(active=False)
```

### Supprimer l'Historique Ancien

```python
from listings.models import PushNotification
from datetime import timedelta

# Supprimer les notifications de plus de 6 mois
cutoff_date = timezone.now() - timedelta(days=180)
PushNotification.objects.filter(created_at__lt=cutoff_date).delete()
```

## Dépannage

### Problème: Les notifications ne sont pas reçues

1. Vérifier que la clé serveur FCM est correcte dans `settings.py`
2. Vérifier que l'appareil est enregistré: `GET /api/fcm/devices/`
3. Vérifier les logs: `tail -f /home/ubuntu/BDD/merchex/logs/django.log`
4. Tester manuellement: `POST /api/fcm/test/`

### Problème: Erreur "InvalidRegistration"

Le token FCM est invalide ou expiré. L'appareil sera automatiquement désactivé.
Solution: Le client doit se réenregistrer avec un nouveau token.

### Problème: ImportError pour pyfcm

```bash
pip install --upgrade pyfcm
```

## Prochaines Améliorations

- [ ] Notifications pour les matchs qui commencent bientôt
- [ ] Notifications personnalisées selon les préférences utilisateur
- [ ] Support de notifications riches (images, boutons d'action)
- [ ] Notifications groupées pour plusieurs paris
- [ ] Analytics détaillées sur les taux d'ouverture

## Support

Pour toute question ou problème, contactez l'équipe de développement Campus League.

---

**Dernière mise à jour:** 2025-11-24
**Version:** 1.0.0
