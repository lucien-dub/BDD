# Configuration des Tâches Automatiques (Cron Jobs)

## Vue d'ensemble

Le projet utilise `django-crontab` pour automatiser l'actualisation des données depuis le site FFSU. Les tâches suivantes sont configurées :

### Tâches planifiées

1. **Actualisation des données de matchs** (toutes les 30 minutes)
   - Récupère les derniers matchs depuis le site FFSU
   - Met à jour les scores, forfaits et autres informations
   - Fonction : `cron.update_matches_data()`

2. **Actualisation des classements** (toutes les 30 minutes)
   - Met à jour les classements des équipes
   - Fonction : `cron.update_classements_data()`

3. **Mise à jour des cotes** (tous les jours à minuit)
   - Recalcule les cotes pour tous les matchs à venir
   - Fonction : `cron.update_all_cotes()`

4. **Réinitialisation des compteurs de connexion** (tous les jours à minuit)
   - Remet à zéro les compteurs de connexion quotidienne
   - Fonction : `cron.reset_login_counters()`

## Installation et activation

### Étape 1 : Vérifier que django-crontab est installé

```bash
pip install django-crontab
```

### Étape 2 : Ajouter les cron jobs au système

```bash
cd merchex
python manage.py crontab add
```

### Étape 3 : Vérifier que les cron jobs sont bien ajoutés

```bash
python manage.py crontab show
```

Vous devriez voir une sortie similaire à :

```
0 0 * * * /path/to/python /path/to/manage.py cron.update_all_cotes
0 0 * * * /path/to/python /path/to/manage.py cron.reset_login_counters
*/30 * * * * /path/to/python /path/to/manage.py cron.update_matches_data
*/30 * * * * /path/to/python /path/to/manage.py cron.update_classements_data
```

## Gestion des cron jobs

### Supprimer tous les cron jobs

```bash
python manage.py crontab remove
```

### Mettre à jour les cron jobs après modification

```bash
python manage.py crontab remove
python manage.py crontab add
```

### Voir les logs

Les logs des tâches cron sont enregistrés dans les logs Django. Pour les voir :

1. Vérifiez la configuration de logging dans `settings.py`
2. Consultez les fichiers de logs ou la console

## Exécution manuelle

Pour tester les fonctions sans attendre l'exécution automatique :

### Actualiser les matchs manuellement

```bash
python manage.py update_matches
```

### Actualiser les classements manuellement

```bash
python manage.py update_classements
```

### Mettre à jour les cotes manuellement

```bash
python manage.py shell
>>> from cron import update_all_cotes
>>> update_all_cotes()
```

## Dépannage

### Les cron jobs ne s'exécutent pas

1. Vérifiez que le service cron est actif :
   ```bash
   # Linux
   sudo service cron status

   # macOS
   sudo launchctl list | grep cron
   ```

2. Vérifiez les logs du cron système :
   ```bash
   # Linux
   grep CRON /var/log/syslog

   # macOS
   log show --predicate 'process == "cron"' --last 1h
   ```

3. Vérifiez que les chemins dans les cron jobs sont corrects :
   ```bash
   python manage.py crontab show
   ```

### Les tâches échouent

1. Vérifiez les logs Django pour voir les erreurs
2. Testez l'exécution manuelle de la commande
3. Vérifiez que tous les modules nécessaires sont installés

### Problèmes de permissions

Si vous obtenez des erreurs de permissions :

```bash
# Linux
sudo chmod +x manage.py
```

## Configuration avancée

### Modifier la fréquence d'exécution

Éditez `merchex/settings.py` et modifiez la variable `CRONJOBS` :

```python
CRONJOBS = [
    # Format : (schedule, function)
    # Schedule au format cron : 'minute hour day month day_of_week'

    # Exemples :
    ('*/15 * * * *', 'cron.update_matches_data'),  # Toutes les 15 minutes
    ('0 */2 * * *', 'cron.update_matches_data'),   # Toutes les 2 heures
    ('0 0,12 * * *', 'cron.update_all_cotes'),     # À minuit et midi
]
```

### Ajouter des arguments aux commandes

```python
CRONJOBS = [
    ('*/30 * * * *', 'django.core.management.call_command', ['ma_commande', '--option']),
]
```

## Environnement de production

Pour un déploiement en production, considérez :

1. **Utiliser Celery** au lieu de django-crontab pour une meilleure gestion des tâches
2. **Configurer des alertes** en cas d'échec des tâches
3. **Monitorer** l'exécution des tâches avec des outils comme Sentry
4. **Logs centralisés** pour suivre l'historique des exécutions

## Référence rapide

| Commande | Description |
|----------|-------------|
| `python manage.py crontab add` | Ajoute les cron jobs au système |
| `python manage.py crontab show` | Affiche les cron jobs actuels |
| `python manage.py crontab remove` | Supprime tous les cron jobs |
| `python manage.py update_matches` | Exécute manuellement la mise à jour des matchs |

## Support

En cas de problème, vérifiez :
- Les logs Django
- Les logs système du cron
- La configuration dans `settings.py`
- Que tous les packages sont installés : `pip install -r requirements.txt`
