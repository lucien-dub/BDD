#!/bin/bash

# Script d'arrêt des services pour serveur TEST
# Usage: ./stop-services-test.sh

echo "🛑 Arrêt des services..."

# Arrêter Daphne
pkill -f daphne && echo "✅ Daphne arrêté" || echo "⚠️  Daphne n'était pas lancé"

# Arrêter Redis
redis-cli shutdown && echo "✅ Redis arrêté" || echo "⚠️  Redis n'était pas lancé"

echo ""
echo "✅ Tous les services sont arrêtés"
