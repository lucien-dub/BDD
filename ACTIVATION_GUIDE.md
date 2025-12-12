# Guide d'activation rapide de l'environnement de production

## 1. Activer l'environnement virtuel Linux

```bash
cd /home/user/BDD  # ou cd ~/BDD
source venv-linux/bin/activate
```

Vous devriez voir `(venv-linux)` apparaître au début de votre ligne de commande.

## 2. Vérifier que Django fonctionne

```bash
cd merchex
python manage.py check
```

Résultat attendu : `System check identified no issues (0 silenced).`

## 3. Installer et activer cron (si pas encore installé)

### Vérifier si cron est installé

```bash
which crontab
```

### Si cron n'est pas installé

```bash
sudo apt-get update
sudo apt-get install -y cron
sudo service cron start
sudo service cron status
```

## 4. Activer les tâches automatiques

```bash
cd /home/user/BDD
source venv-linux/bin/activate
cd merchex
python manage.py crontab add
```

## 5. Vérifier que les cron jobs sont actifs

```bash
python manage.py crontab show
```

Vous devriez voir :

```
0 0 * * * ... cron.update_all_cotes
0 0 * * * ... cron.reset_login_counters
*/30 * * * * ... cron.update_matches_data
*/30 * * * * ... cron.update_classements_data
```

## 6. Tester manuellement l'actualisation des données

```bash
python manage.py update_matches
```

## 7. Lancer le serveur Django

### Mode développement

```bash
python manage.py runserver 0.0.0.0:8000
```

### Mode production (avec Gunicorn)

```bash
# Installer Gunicorn si nécessaire
pip install gunicorn

# Lancer le serveur
gunicorn merchex.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## 8. Vérifier les logs

```bash
# Voir les logs Django
tail -f logs/django.log

# Voir les logs du cron système
grep CRON /var/log/syslog | tail -20
```

## Résumé des tâches automatiques

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| `update_matches_data` | Toutes les 30 min | Actualise les matchs depuis FFSU |
| `update_classements_data` | Toutes les 30 min | Actualise les classements |
| `update_all_cotes` | Quotidien à minuit | Recalcule les cotes |
| `reset_login_counters` | Quotidien à minuit | Réinitialise les compteurs de connexion |

## Commandes utiles

### Gérer les cron jobs

```bash
# Ajouter les cron jobs
python manage.py crontab add

# Voir les cron jobs actifs
python manage.py crontab show

# Supprimer tous les cron jobs
python manage.py crontab remove
```

### Migrations Django

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

### Gestion des utilisateurs

```bash
# Créer un superutilisateur
python manage.py createsuperuser
```

## Dépannage

### "ModuleNotFoundError: No module named 'django'"

Assurez-vous que l'environnement virtuel est activé :

```bash
source /home/user/BDD/venv-linux/bin/activate
```

### Les cron jobs ne s'exécutent pas

1. Vérifier que cron est actif :
   ```bash
   sudo service cron status
   ```

2. Vérifier les logs :
   ```bash
   grep CRON /var/log/syslog | tail -20
   ```

3. Relancer les cron jobs :
   ```bash
   python manage.py crontab remove
   python manage.py crontab add
   ```

### Erreur de permissions

Si vous obtenez des erreurs de permissions :

```bash
# Donner les bonnes permissions aux dossiers
chmod -R 755 /home/user/BDD/merchex
chmod +x /home/user/BDD/merchex/manage.py

# Créer le dossier logs s'il n'existe pas
mkdir -p /home/user/BDD/merchex/logs
touch /home/user/BDD/merchex/logs/django.log
```

## Maintenance

### Sauvegarder la base de données

```bash
cd /home/user/BDD/merchex
python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

### Nettoyer les anciennes données

```bash
# Supprimer les sessions expirées
python manage.py clearsessions
```

### Mettre à jour les dépendances

```bash
source venv-linux/bin/activate
pip install -r requirements.txt --upgrade
```

## Production checklist

- [ ] Environnement virtuel activé
- [ ] Django check sans erreurs
- [ ] Cron installé et actif
- [ ] Cron jobs ajoutés et vérifiés
- [ ] Base de données migrée
- [ ] Superutilisateur créé
- [ ] Serveur de production configuré (Gunicorn/Nginx)
- [ ] Variables d'environnement sécurisées
- [ ] DEBUG=False dans settings.py
- [ ] ALLOWED_HOSTS configuré
- [ ] Logs rotatifs configurés
