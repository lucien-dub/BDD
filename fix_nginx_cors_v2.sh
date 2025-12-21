#!/bin/bash

echo "🔧 FIX NGINX CORS - VERSION 2 (Compatible django-cors-headers)"
echo "================================================================"
echo ""

# Backup the current configuration
echo "📋 Backing up current nginx configuration..."
sudo cp /etc/nginx/sites-available/campus-league.com /etc/nginx/sites-available/campus-league.com.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Create the updated configuration that works with django-cors-headers
echo "📝 Creating updated nginx configuration compatible with django-cors-headers..."
sudo tee /etc/nginx/sites-available/campus-league.com > /dev/null <<'EOF'
server {
    listen 80;
    server_name test.campus-league.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name test.campus-league.com;

    ssl_certificate /etc/letsencrypt/live/campus-league.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/campus-league.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10M;

    location / {
        # Proxy tout vers Django (qui gère déjà CORS via django-cors-headers)
        proxy_pass http://127.0.0.1:8001;

        # Headers proxy standards
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Désactiver le buffering pour les réponses en temps réel
        proxy_buffering off;
        proxy_redirect off;

        # Augmenter les timeouts pour les requêtes longues
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/ubuntu/BDD-test/merchex/static/;
    }

    location /media/ {
        alias /home/ubuntu/BDD-test/merchex/media/;
    }
}
EOF

echo "✅ Configuration updated to work with django-cors-headers"
echo ""

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo ""

    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx

    if [ $? -eq 0 ]; then
        echo "✅ Nginx reloaded successfully"
    else
        echo "❌ Failed to reload nginx"
        exit 1
    fi
else
    echo "❌ Nginx configuration test failed"
    echo "⚠️  Restoring backup..."
    sudo cp /etc/nginx/sites-available/campus-league.com.backup.$(date +%Y%m%d)* /etc/nginx/sites-available/campus-league.com
    echo "Backup restored. Please check the configuration manually."
    exit 1
fi

echo ""
echo "================================"
echo "✅ CONFIGURATION COMPLETE"
echo "================================"
echo ""
echo "🧪 Testing endpoints..."
echo ""
echo "Test 1: OPTIONS request to /api/academies/available/"
curl -X OPTIONS https://test.campus-league.com/api/academies/available/ \
  -H "Origin: http://localhost:8100" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -i | head -20

echo ""
echo "Test 2: GET request to /api/academies/available/"
curl -X GET https://test.campus-league.com/api/academies/available/ \
  -H "Origin: http://localhost:8100" \
  -i | head -20

echo ""
echo "✅ Script completed!"
echo "Django CORS headers should now pass through nginx correctly."
