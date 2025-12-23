# 📋 Checklist Frontend - WebSocket Cotes en Temps Réel

## 🎯 Vue d'ensemble

Cette checklist vous guide pour intégrer le WebSocket des cotes en temps réel dans votre application React/TypeScript.

---

## ✅ Tâche 1 : Créer le service WebSocket

### Fichier : `src/services/websocketService.ts`

```typescript
class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<Function>> = new Map();

  /**
   * Connexion au WebSocket
   * @param matchId - ID du match spécifique, ou 'all' pour tous les matchs
   */
  connect(matchId: string | 'all' = 'all') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/cotes/${matchId !== 'all' ? matchId + '/' : ''}`;

    console.log('[WebSocket] Connexion à:', url);

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log('[WebSocket] Connecté');
      this.reconnectAttempts = 0;
      this.emit('connected', null);
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] Message reçu:', data);

        if (data.type === 'cotes_update') {
          this.emit('cotes_update', data.data);
        } else if (data.type === 'cotes_initial') {
          this.emit('cotes_initial', data.data);
        }
      } catch (error) {
        console.error('[WebSocket] Erreur parsing JSON:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('[WebSocket] Erreur:', error);
      this.emit('error', error);
    };

    this.socket.onclose = (event) => {
      console.log('[WebSocket] Déconnecté:', event.code, event.reason);
      this.emit('disconnected', null);
      this.reconnect();
    };
  }

  /**
   * Reconnexion automatique
   */
  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`[WebSocket] Reconnexion dans ${delay}ms (tentative ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('[WebSocket] Nombre maximum de tentatives de reconnexion atteint');
      this.emit('max_reconnect_attempts_reached', null);
    }
  }

  /**
   * Envoyer un message au serveur
   */
  send(message: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Impossible d\'envoyer, socket non connecté');
    }
  }

  /**
   * S'abonner à un événement
   */
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  /**
   * Se désabonner d'un événement
   */
  off(event: string, callback: Function) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.delete(callback);
    }
  }

  /**
   * Émettre un événement
   */
  private emit(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => callback(data));
    }
  }

  /**
   * Déconnexion
   */
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.listeners.clear();
  }

  /**
   * Vérifier si connecté
   */
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// Export instance singleton
export const websocketService = new WebSocketService();
```

**✅ Checklist :**
- [ ] Fichier créé : `src/services/websocketService.ts`
- [ ] Import ajouté dans les composants qui en ont besoin
- [ ] Testé en dev : `console.log` visible dans la console
- [ ] Gestion de reconnexion testée (couper/rétablir connexion)

---

## ✅ Tâche 2 : Hook React personnalisé

### Fichier : `src/hooks/useCotesWebSocket.ts`

```typescript
import { useEffect, useState, useCallback } from 'react';
import { websocketService } from '../services/websocketService';

interface CoteData {
  match_id: number;
  cote1: number;
  cote2: number;
  coteN: number;
  last_updated: string;
  paris_count: number;
  match: {
    equipe1: string;
    equipe2: string;
    date: string;
    heure: string;
  };
}

interface UseCotesWebSocketOptions {
  matchId?: string | 'all';
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export const useCotesWebSocket = (options: UseCotesWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [cotes, setCotes] = useState<Map<number, CoteData>>(new Map());
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const { matchId = 'all', onConnect, onDisconnect, onError } = options;

  // Callback pour mise à jour d'une cote
  const handleCoteUpdate = useCallback((data: CoteData) => {
    setCotes(prev => {
      const newCotes = new Map(prev);
      newCotes.set(data.match_id, data);
      return newCotes;
    });
    setLastUpdate(new Date());
  }, []);

  // Callback pour cotes initiales
  const handleCotesInitial = useCallback((data: CoteData[]) => {
    const newCotes = new Map<number, CoteData>();
    data.forEach(cote => {
      newCotes.set(cote.match_id, cote);
    });
    setCotes(newCotes);
    setLastUpdate(new Date());
  }, []);

  // Connexion au WebSocket
  useEffect(() => {
    websocketService.connect(matchId);

    // Event handlers
    const handleConnected = () => {
      setIsConnected(true);
      onConnect?.();
    };

    const handleDisconnected = () => {
      setIsConnected(false);
      onDisconnect?.();
    };

    const handleError = (error: any) => {
      onError?.(error);
    };

    // Subscribe to events
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('error', handleError);
    websocketService.on('cotes_update', handleCoteUpdate);
    websocketService.on('cotes_initial', handleCotesInitial);

    // Cleanup
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('error', handleError);
      websocketService.off('cotes_update', handleCoteUpdate);
      websocketService.off('cotes_initial', handleCotesInitial);
      websocketService.disconnect();
    };
  }, [matchId, onConnect, onDisconnect, onError, handleCoteUpdate, handleCotesInitial]);

  // Fonction pour obtenir une cote spécifique
  const getCote = useCallback((matchId: number): CoteData | undefined => {
    return cotes.get(matchId);
  }, [cotes]);

  return {
    isConnected,
    cotes: Array.from(cotes.values()),
    getCote,
    lastUpdate
  };
};
```

**✅ Checklist :**
- [ ] Fichier créé : `src/hooks/useCotesWebSocket.ts`
- [ ] Types TypeScript définis correctement
- [ ] Hook testé dans un composant
- [ ] Pas de memory leaks (vérifier avec React DevTools)

---

## ✅ Tâche 3 : Composant d'affichage des cotes

### Fichier : `src/components/CoteDisplay.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { useCotesWebSocket } from '../hooks/useCotesWebSocket';
import './CoteDisplay.css';  // Voir CSS ci-dessous

interface CoteDisplayProps {
  matchId: number;
}

export const CoteDisplay: React.FC<CoteDisplayProps> = ({ matchId }) => {
  const { getCote, isConnected } = useCotesWebSocket({ matchId: 'all' });
  const cote = getCote(matchId);

  const [animatedCotes, setAnimatedCotes] = useState({
    cote1: false,
    cote2: false,
    coteN: false
  });

  // Déclencher animation quand les cotes changent
  useEffect(() => {
    if (cote) {
      setAnimatedCotes({ cote1: true, cote2: true, coteN: true });
      const timer = setTimeout(() => {
        setAnimatedCotes({ cote1: false, cote2: false, coteN: false });
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [cote?.cote1, cote?.cote2, cote?.coteN]);

  if (!cote) {
    return <div className="cote-loading">Chargement des cotes...</div>;
  }

  return (
    <div className="cote-container" data-match-id={matchId}>
      {/* Indicateur de connexion */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 En direct' : '🔴 Déconnecté'}
      </div>

      {/* Cotes */}
      <div className="cotes-row">
        <div className={`cote-item ${animatedCotes.cote1 ? 'cote-changed' : ''}`}>
          <span className="cote-label">{cote.match.equipe1}</span>
          <span className="cote-value">{cote.cote1.toFixed(2)}</span>
        </div>

        <div className={`cote-item ${animatedCotes.coteN ? 'cote-changed' : ''}`}>
          <span className="cote-label">Nul</span>
          <span className="cote-value">{cote.coteN.toFixed(2)}</span>
        </div>

        <div className={`cote-item ${animatedCotes.cote2 ? 'cote-changed' : ''}`}>
          <span className="cote-label">{cote.match.equipe2}</span>
          <span className="cote-value">{cote.cote2.toFixed(2)}</span>
        </div>
      </div>

      {/* Info supplémentaires */}
      <div className="cote-info">
        <span className="paris-count">{cote.paris_count} paris depuis MAJ</span>
        <span className="last-updated">
          Mis à jour: {new Date(cote.last_updated).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};
```

**✅ Checklist :**
- [ ] Composant créé : `src/components/CoteDisplay.tsx`
- [ ] Intégré dans la page de matchs
- [ ] Animation de changement visible
- [ ] Indicateur de connexion fonctionne

---

## ✅ Tâche 4 : CSS pour les animations

### Fichier : `src/components/CoteDisplay.css`

```css
.cote-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  margin: 10px 0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.connection-status {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 10px;
  padding: 5px 10px;
  border-radius: 20px;
  display: inline-block;
}

.connection-status.connected {
  background: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
}

.connection-status.disconnected {
  background: rgba(244, 67, 54, 0.2);
  color: #F44336;
}

.cotes-row {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin: 15px 0;
}

.cote-item {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.cote-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.cote-item.cote-changed {
  animation: pulse 1s ease-in-out;
  background: #FFD700;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.cote-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.cote-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.cote-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 10px;
}

.cote-loading {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}
```

**✅ Checklist :**
- [ ] Fichier CSS créé
- [ ] Animations fonctionnent (effet pulse au changement)
- [ ] Responsive (mobile et desktop)
- [ ] Couleurs correspondent à la charte graphique

---

## ✅ Tâche 5 : Intégration dans la page principale

### Exemple : `src/pages/MatchsPage.tsx`

```typescript
import React from 'react';
import { CoteDisplay } from '../components/CoteDisplay';

export const MatchsPage: React.FC = () => {
  const [matches, setMatches] = useState([/* ... vos matchs ... */]);

  return (
    <div className="matchs-page">
      <h1>Matchs disponibles</h1>

      {matches.map(match => (
        <div key={match.id} className="match-card">
          {/* Infos du match */}
          <div className="match-header">
            <h3>{match.equipe1} vs {match.equipe2}</h3>
            <span className="match-date">
              {new Date(match.date).toLocaleDateString()} - {match.heure}
            </span>
          </div>

          {/* Cotes en temps réel */}
          <CoteDisplay matchId={match.id} />

          {/* Bouton parier */}
          <button className="btn-parier">Parier</button>
        </div>
      ))}
    </div>
  );
};
```

**✅ Checklist :**
- [ ] `CoteDisplay` intégré dans la page des matchs
- [ ] Cotes s'affichent correctement pour chaque match
- [ ] Animations visibles quand un autre utilisateur parie
- [ ] Pas de ralentissement avec beaucoup de matchs

---

## ✅ Tâche 6 : Gestion d'erreurs et notifications

### Fichier : `src/components/WebSocketStatus.tsx`

```typescript
import React from 'react';
import { useCotesWebSocket } from '../hooks/useCotesWebSocket';

export const WebSocketStatus: React.FC = () => {
  const { isConnected, lastUpdate } = useCotesWebSocket({
    onConnect: () => {
      console.log('✅ WebSocket connecté');
      // Optionnel: toast notification
    },
    onDisconnect: () => {
      console.warn('⚠️ WebSocket déconnecté, tentative de reconnexion...');
      // Optionnel: toast notification
    },
    onError: (error) => {
      console.error('❌ Erreur WebSocket:', error);
      // Optionnel: toast notification
    }
  });

  return (
    <div className={`websocket-status-badge ${isConnected ? 'online' : 'offline'}`}>
      {isConnected ? (
        <>
          🟢 Cotes en direct
          {lastUpdate && (
            <span className="last-update">
              Dernière MAJ: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </>
      ) : (
        <>
          🔴 Reconnexion en cours...
        </>
      )}
    </div>
  );
};
```

**✅ Checklist :**
- [ ] Badge de statut affiché dans le header
- [ ] Notifications toast (optionnel)
- [ ] Message clair en cas de déconnexion

---

## ✅ Tâche 7 : Tests

### Tests à effectuer

#### Test 1 : Connexion initiale
1. Ouvrir l'application
2. Vérifier console : `[WebSocket] Connecté`
3. Vérifier que les cotes s'affichent
4. Badge "🟢 En direct" visible

**✅ Test réussi :** [ ]

#### Test 2 : Mise à jour en temps réel
1. Ouvrir 2 navigateurs (ou 2 onglets)
2. Sur navigateur A : placer un pari sur un match
3. Sur navigateur B : observer l'animation de changement de cotes

**✅ Test réussi :** [ ]

#### Test 3 : Reconnexion
1. Ouvrir l'application
2. Couper la connexion internet 10 secondes
3. Rétablir la connexion
4. Vérifier reconnexion automatique

**✅ Test réussi :** [ ]

#### Test 4 : Performance
1. Ouvrir page avec 20+ matchs
2. Vérifier que l'application ne lag pas
3. Vérifier FPS dans DevTools > Performance

**✅ Test réussi :** [ ]

---

## ✅ Tâche 8 : Optimisations

### À faire avant production

- [ ] **Throttling** : Limiter la fréquence de mise à jour UI (max 1x/seconde)
- [ ] **Lazy loading** : Connecter WebSocket uniquement sur page active
- [ ] **Cleanup** : Déconnecter WebSocket quand l'utilisateur quitte la page
- [ ] **Error boundaries** : Wrapper les composants WebSocket dans ErrorBoundary
- [ ] **Service Worker** : Gérer les notifications en background (optionnel)

---

## 📊 Checklist Finale

### Backend
- [ ] Redis installé et configuré
- [ ] Daphne installé et running (port 8002)
- [ ] Nginx configuré pour proxy WebSocket
- [ ] Migrations appliquées
- [ ] Logs vérifiés : `[WEBSOCKET] Client connecté`

### Frontend
- [ ] Service WebSocket créé
- [ ] Hook `useCotesWebSocket` créé
- [ ] Composant `CoteDisplay` créé
- [ ] CSS et animations ajoutés
- [ ] Intégré dans page principale
- [ ] Tests effectués
- [ ] Performance vérifiée

### Production
- [ ] HTTPS/WSS configuré
- [ ] Redis sécurisé (password)
- [ ] Logs de production configurés
- [ ] Monitoring en place
- [ ] Documentation utilisateur

---

## 🎉 Résultat final

Quand tout est fait, vos utilisateurs verront :
- ✅ Cotes qui changent en temps réel avec animation
- ✅ Indicateur "🟢 En direct" toujours visible
- ✅ Compteur de paris qui s'incrémente
- ✅ Experience fluide et immersive

**Bonne chance ! 🚀**
