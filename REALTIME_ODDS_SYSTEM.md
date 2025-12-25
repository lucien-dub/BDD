# Système de Cotes en Temps Réel

## 📋 Vue d'ensemble

Le système de cotes en temps réel recalcule automatiquement les cotes d'un match après un certain nombre de nouveaux paris.

## ⚙️ Fonctionnement

### 1. Détection automatique
Quand un utilisateur place un pari :
- Un **signal Django** (`post_save` sur le modèle `Pari`) se déclenche
- Le compteur `paris_count_since_last_update` s'incrémente pour le match concerné

### 2. Seuil de recalcul
- **Seuil par défaut** : 5 paris
- Quand le seuil est atteint → recalcul automatique des cotes
- Le compteur est réinitialisé à 0

### 3. Recalcul des cotes
- Utilise la fonction existante `calculer_cotes()` de `background/odds_calculator.py`
- Prend en compte tous les paris pour ajuster les probabilités
- Met à jour `cote1`, `cote2`, `coteN`

## 🔧 Configuration

### Modifier le seuil de recalcul

Dans `merchex/listings/models.py`, classe `Cote` :

```python
class Cote(models.Model):
    # ...
    RECALCUL_THRESHOLD = 5  # ← Modifier ici
```

**Exemples de configurations** :
- `RECALCUL_THRESHOLD = 3` → Recalcul très fréquent (réactif)
- `RECALCUL_THRESHOLD = 10` → Recalcul moins fréquent (performant)
- `RECALCUL_THRESHOLD = 1` → Recalcul à chaque pari (max réactivité)

### Désactiver le recalcul automatique

Si vous voulez désactiver temporairement :

```python
def increment_paris_count(self):
    self.paris_count_since_last_update += 1
    self.save()
    # Commenter la ligne ci-dessous pour désactiver
    # if self.paris_count_since_last_update >= self.RECALCUL_THRESHOLD:
    #     self.recalculer_cotes()
```

## 📊 Nouveaux champs du modèle Cote

| Champ | Type | Description |
|-------|------|-------------|
| `paris_count_since_last_update` | IntegerField | Nombre de paris depuis le dernier recalcul |
| `last_updated` | DateTimeField | Date/heure du dernier recalcul |

## 🚀 Déploiement

### 1. Appliquer la migration

```bash
cd /home/ubuntu/BDD-test/merchex
source /home/ubuntu/BDD-test/venv-test/bin/activate
python manage.py migrate listings
```

### 2. Redémarrer Gunicorn

```bash
sudo /home/ubuntu/BDD-test/deploy_to_test.sh
```

### 3. Vérifier les logs

```bash
tail -f /tmp/gunicorn-test.log | grep COTES
```

Vous devriez voir des logs comme :
```
[COTES] Nouveau pari sur match 123. Compteur: 1/5
[COTES] Nouveau pari sur match 123. Compteur: 2/5
...
[COTES] Nouveau pari sur match 123. Compteur: 5/5
[INFO] Recalcul des cotes pour le match 123
```

## 📈 Monitoring

### API pour voir l'état des cotes

L'endpoint `/api/cotes/` retourne maintenant aussi :
```json
{
  "match_id": 123,
  "cote1": 2.35,
  "cote2": 1.85,
  "coteN": 3.20,
  "paris_count_since_last_update": 3,
  "last_updated": "2024-12-23T15:30:00Z"
}
```

### Forcer un recalcul manuel

Endpoint existant : `GET /api/update-cotes/?match_id=123`

## ⚡ Performance

### Avantages
- ✅ Cotes toujours à jour
- ✅ Distribution automatique de la charge
- ✅ Pas de recalcul inutile si peu de paris

### Optimisations possibles

**Pour les gros volumes** :
- Utiliser Celery pour recalcul asynchrone
- Mettre en cache les cotes avec Redis
- Augmenter le seuil de recalcul

## 🐛 Dépannage

### Les cotes ne se mettent pas à jour

1. Vérifier les logs : `tail -f /tmp/gunicorn-test.log | grep COTES`
2. Vérifier le signal : `python manage.py shell`
   ```python
   from django.db.models.signals import post_save
   print(post_save.receivers)  # Vérifier que le signal est enregistré
   ```
3. Vérifier le seuil : tester avec `RECALCUL_THRESHOLD = 1`

### Erreurs dans les logs

Si vous voyez des erreurs de type "module background.odds_calculator not found" :
- Vérifier que le module existe : `ls merchex/background/odds_calculator.py`
- Vérifier l'import dans `models.py`

## 📝 Notes techniques

- Le signal se déclenche **uniquement à la création** d'un pari (`created=True`)
- Le recalcul est **synchrone** (bloque la requête)
- Les cotes sont arrondies à 2 décimales
- Le système est compatible avec les matchs multiples (paris combinés)

## 🔄 Évolutions futures possibles

1. **Recalcul asynchrone avec Celery**
   ```python
   @shared_task
   def recalculer_cotes_async(match_id):
       calculer_cotes(match_id)
   ```

2. **WebSocket pour notifier le frontend**
   - Les clients voient les cotes changer en temps réel
   - Utiliser Django Channels

3. **Seuil adaptatif**
   - Seuil plus bas pour les gros matchs
   - Seuil plus haut pour les petits matchs

4. **Historique des cotes**
   - Stocker l'évolution des cotes dans le temps
   - Graphiques d'évolution

---

**Créé le** : 2024-12-23
**Version** : 1.0
**Auteur** : Claude Code
