#!/bin/bash

echo "🔧 FIX NGINX CORS CONFIGURATION"
echo "================================"
echo ""

# Backup the current configuration
echo "📋 Backing up current nginx configuration..."
sudo cp /etc/nginx/sites-available/campus-league.com /etc/nginx/sites-available/campus-league.com.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup created"
echo ""

# Create the updated configuration with CORS headers
echo "📝 Creating updated nginx configuration with CORS headers..."
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
        # CORS Headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Accept, Accept-Encoding, Authorization, Content-Type, DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;

        # Handle preflight OPTIONS requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Accept, Accept-Encoding, Authorization, Content-Type, DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }

        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/ubuntu/BDD-test/merchex/static/;
    }

    location /media/ {
        alias /home/ubuntu/BDD-test/merchex/media/;
    }
}
EOF

echo "✅ Configuration updated with CORS headers"
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
echo "✅ CORS CONFIGURATION COMPLETE"
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
echo "If you see 'Access-Control-Allow-Origin: *' in the headers above, CORS is working!"
