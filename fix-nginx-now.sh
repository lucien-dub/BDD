#!/bin/bash
# Script de correction Nginx - À exécuter sur le serveur hôte

echo "🔧 Correction de la configuration Nginx..."

# 1. Supprimer le fichier incorrect
echo "1. Suppression du fichier incorrect..."
sudo rm -f /etc/nginx/sites-enabled/test.campus-league.com
sudo rm -f /etc/nginx/sites-available/test.campus-league.com

# 2. Vérifier la configuration
echo "2. Test de la configuration Nginx..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration Nginx OK après suppression du fichier incorrect"
    echo ""
    echo "📝 Maintenant, éditez le fichier principal :"
    echo "   sudo nano /etc/nginx/sites-available/campus-league.com"
    echo ""
    echo "   Trouvez le bloc 'server' avec 'test.campus-league.com'"
    echo "   et ajoutez la section location /ws/ AVANT location /"
else
    echo "❌ Il reste des erreurs dans la configuration"
    sudo nginx -t
fi
