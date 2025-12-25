#!/bin/bash
# Script pour créer le service systemd Daphne

cat << 'EOF' | sudo tee /etc/systemd/system/daphne-test.service
[Unit]
Description=Daphne ASGI Server pour Campus League Test
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/BDD-test/merchex
ExecStart=/home/ubuntu/BDD-test/venv-test/bin/daphne -b 0.0.0.0 -p 8002 merchex.asgi:application
Restart=always
RestartSec=3

# Logs
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Fichier de service créé : /etc/systemd/system/daphne-test.service"
echo ""
echo "Prochaines étapes :"
echo "1. sudo systemctl daemon-reload"
echo "2. sudo systemctl start daphne-test"
echo "3. sudo systemctl enable daphne-test"
echo "4. sudo systemctl status daphne-test"
