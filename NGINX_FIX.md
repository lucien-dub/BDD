# 🔧 Correction Configuration Nginx WebSocket

## ❌ Problème

Vous avez créé un fichier avec seulement :
```nginx
location /ws/ {
    ...
}
```

Cette directive `location` doit être **à l'intérieur** d'un bloc `server`.

## ✅ Solution

### Option 1 : Ajouter à la configuration existante (RECOMMANDÉ)

Éditez votre fichier de configuration principal :

```bash
sudo nano /etc/nginx/sites-available/campus-league.com
```

Trouvez le bloc `server` pour votre domaine test, et **ajoutez** la section WebSocket :

```nginx
server {
    listen 80;
    server_name test.campus-league.com www.test.campus-league.com;

    # ... vos autres configurations existantes ...

    # ⬇️ AJOUTER CETTE SECTION ICI
    # WebSocket pour cotes en temps réel
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # Vos autres locations existantes (/, /api/, etc.)
    location / {
        # ... votre config existante ...
    }
}
```

### Option 2 : Supprimer le fichier incorrect

Si vous avez créé un fichier séparé `test.campus-league.com` avec juste la section location :

```bash
# Supprimer le lien symbolique incorrect
sudo rm /etc/nginx/sites-enabled/test.campus-league.com

# Supprimer le fichier incorrect (si créé)
sudo rm /etc/nginx/sites-available/test.campus-league.com

# Tester la config
sudo nginx -t
```

Puis suivez l'Option 1 pour ajouter la section dans votre fichier principal.

## 📋 Étapes détaillées

### 1. Vérifier quel fichier nginx utilise actuellement

```bash
# Voir tous les fichiers de config actifs
sudo ls -la /etc/nginx/sites-enabled/

# Afficher le fichier principal
sudo cat /etc/nginx/sites-enabled/campus-league.com
```

### 2. Éditer le bon fichier

```bash
# Éditer le fichier principal
sudo nano /etc/nginx/sites-available/campus-league.com
```

### 3. Ajouter la section WebSocket

**IMPORTANT** : Placez la section `/ws/` **AVANT** les autres locations (surtout avant `location /`)

```nginx
server {
    # ... config existante ...

    # WebSocket - DOIT être AVANT location /
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # API REST
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Autres routes
    location / {
        # ... votre config existante ...
    }
}
```

### 4. Tester et recharger

```bash
# Tester la syntaxe
sudo nginx -t

# Si OK, recharger nginx
sudo systemctl reload nginx

# Vérifier le statut
sudo systemctl status nginx
```

## 🧪 Test rapide

```bash
# Test depuis le serveur
curl -i http://test.campus-league.com/ws/cotes/

# Devrait retourner 426 Upgrade Required ou 101 Switching Protocols
```

## 📝 Exemple complet d'un bloc server

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name test.campus-league.com www.test.campus-league.com;

    access_log /var/log/nginx/test.access.log;
    error_log /var/log/nginx/test.error.log;

    # WebSocket (AVANT les autres locations)
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/user/BDD/merchex/staticfiles/;
        expires 30d;
    }

    # Toutes les autres requêtes
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
