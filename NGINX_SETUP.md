# 🔧 Configuration Nginx pour WebSocket

## 📋 Instructions pour le serveur TEST

### 1️⃣ Copier la configuration

Sur le **serveur hôte** (pas dans le conteneur), copiez le fichier de configuration :

```bash
# Option A: Si vous avez accès direct au serveur hôte
sudo cp /path/to/nginx-websocket-config.conf /etc/nginx/sites-available/test.campus-league.com

# Option B: Copier manuellement le contenu
sudo nano /etc/nginx/sites-available/test.campus-league.com
# Puis coller le contenu de nginx-websocket-config.conf
```

### 2️⃣ Activer le site

```bash
# Créer le lien symbolique
sudo ln -s /etc/nginx/sites-available/test.campus-league.com /etc/nginx/sites-enabled/

# Désactiver la config par défaut si nécessaire
sudo rm /etc/nginx/sites-enabled/default
```

### 3️⃣ Tester la configuration

```bash
# Vérifier la syntaxe nginx
sudo nginx -t

# Si OK, vous devriez voir :
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 4️⃣ Recharger Nginx

```bash
# Recharger la configuration (sans interruption)
sudo systemctl reload nginx

# OU redémarrer nginx (avec courte interruption)
sudo systemctl restart nginx

# Vérifier le statut
sudo systemctl status nginx
```

### 5️⃣ Vérifier les logs en cas d'erreur

```bash
# Logs d'erreur Nginx
sudo tail -f /var/log/nginx/error.log

# Logs d'accès
sudo tail -f /var/log/nginx/test.campus-league.access.log
```

---

## 🧪 Tester le WebSocket

### Depuis la ligne de commande :

```bash
# Test basique (devrait retourner 101 Switching Protocols)
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: test.campus-league.com" \
  -H "Origin: http://test.campus-league.com" \
  http://test.campus-league.com/ws/cotes/
```

### Depuis le navigateur (Console DevTools) :

```javascript
// Test de connexion WebSocket
const ws = new WebSocket('ws://test.campus-league.com/ws/cotes/');

ws.onopen = () => console.log('✅ Connecté au WebSocket');
ws.onmessage = (event) => console.log('📨 Message reçu:', event.data);
ws.onerror = (error) => console.error('❌ Erreur:', error);
ws.onclose = () => console.log('🔌 Déconnecté');
```

---

## 🔒 Configuration SSL/HTTPS (Recommandé pour production)

### Installer Certbot (Let's Encrypt)

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### Obtenir un certificat SSL

```bash
sudo certbot --nginx -d test.campus-league.com -d www.test.campus-league.com
```

### Le WebSocket utilisera alors WSS au lieu de WS

```javascript
// Frontend avec SSL
const ws = new WebSocket('wss://test.campus-league.com/ws/cotes/');
```

---

## 🐛 Dépannage

### Erreur 502 Bad Gateway

```bash
# Vérifier que Daphne tourne
ps aux | grep daphne

# Vérifier que le port 8002 est à l'écoute
netstat -tlnp | grep 8002

# Redémarrer Daphne si nécessaire
cd /home/user/BDD
./stop-services-test.sh
./start-services-test.sh
```

### Erreur 404 sur /ws/

```bash
# Vérifier la configuration nginx
sudo nginx -t

# Vérifier que la location /ws/ est bien présente
sudo grep -A 10 "location /ws/" /etc/nginx/sites-available/test.campus-league.com
```

### WebSocket se déconnecte immédiatement

```bash
# Vérifier les logs Daphne
tail -f /tmp/daphne-test.log

# Vérifier les logs nginx
sudo tail -f /var/log/nginx/test.campus-league.error.log

# Vérifier que Redis tourne
redis-cli ping
```

---

## 📊 Monitoring

### Voir les connexions WebSocket actives

```bash
# Connexions actives sur port 8002
sudo netstat -anp | grep :8002 | grep ESTABLISHED

# Ou avec ss
sudo ss -anp | grep :8002 | grep ESTABLISHED
```

### Logs en temps réel

```bash
# Terminal 1 : Logs Daphne
tail -f /tmp/daphne-test.log

# Terminal 2 : Logs Nginx
sudo tail -f /var/log/nginx/test.campus-league.access.log

# Terminal 3 : Logs Redis (si verbose)
redis-cli monitor
```

---

## 🎯 URLs finales

Après configuration :

- **WebSocket (tous matchs)** : `ws://test.campus-league.com/ws/cotes/`
- **WebSocket (match ID 123)** : `ws://test.campus-league.com/ws/cotes/123/`
- **API REST** : `http://test.campus-league.com/api/matches/filtered/`
- **Admin Django** : `http://test.campus-league.com/admin/`

Avec SSL :
- **WebSocket (tous matchs)** : `wss://test.campus-league.com/ws/cotes/`
- **API REST** : `https://test.campus-league.com/api/matches/filtered/`
