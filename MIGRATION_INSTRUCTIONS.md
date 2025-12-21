# Instructions de Migration - Optimisations Backend

## Étapes pour appliquer les changements

Après avoir activé votre environnement virtuel, exécutez les commandes suivantes :

```bash
# 1. Créer les migrations
cd /home/user/BDD/merchex
python manage.py makemigrations listings

# 2. Afficher les migrations créées
python manage.py sqlmigrate listings <numero_migration>

# 3. Appliquer les migrations
python manage.py migrate listings
```

## Changements de modèles effectués

### 1. Conversion FloatField → DecimalField

**Modèle Cote:**
- `coteN`: FloatField → DecimalField(max_digits=5, decimal_places=2, default=1.10)
- `cote1`: FloatField → DecimalField(max_digits=5, decimal_places=2, default=1.10)
- `cote2`: FloatField → DecimalField(max_digits=5, decimal_places=2, default=1.10)

**Modèle Bet:**
- `mise`: FloatField → DecimalField(max_digits=10, decimal_places=2, default=0)
- `cote_totale`: FloatField → DecimalField(max_digits=5, decimal_places=2, default=1)
- `annule`: BooleanField(default='False') → BooleanField(default=False)

### 2. Ajout d'index pour les performances

**Modèle Match:**
```python
indexes = [
    models.Index(fields=['sport', 'date']),
    models.Index(fields=['academie', 'date']),
    models.Index(fields=['date', 'heure']),
    models.Index(fields=['sport', 'niveau']),
]
```

**Modèle Bet:**
```python
indexes = [
    models.Index(fields=['user', 'actif']),
    models.Index(fields=['user', '-date_creation']),
    models.Index(fields=['actif', '-date_creation']),
]
```

**Modèle Pari:**
```python
indexes = [
    models.Index(fields=['match', 'actif']),
    models.Index(fields=['bet', 'actif']),
    models.Index(fields=['actif', 'resultat']),
]
```

## Migration manuelle si nécessaire

Si vous rencontrez des problèmes avec makemigrations, voici le SQL approximatif pour SQLite :

```sql
-- Conversion des cotes (FloatField → DecimalField)
-- SQLite ne supporte pas ALTER COLUMN directement, donc :
-- 1. Créer une table temporaire
-- 2. Copier les données
-- 3. Supprimer l'ancienne table
-- 4. Renommer la nouvelle table

-- Pour les index :
CREATE INDEX idx_match_sport_date ON creation_bdd_match (sport, date);
CREATE INDEX idx_match_academie_date ON creation_bdd_match (academie, date);
CREATE INDEX idx_match_date_heure ON creation_bdd_match (date, heure);
CREATE INDEX idx_match_sport_niveau ON creation_bdd_match (sport, niveau);

CREATE INDEX idx_bet_user_actif ON listings_bet (user_id, actif);
CREATE INDEX idx_bet_user_date ON listings_bet (user_id, date_creation DESC);
CREATE INDEX idx_bet_actif_date ON listings_bet (actif, date_creation DESC);

CREATE INDEX idx_pari_match_actif ON listings_pari (match_id, actif);
CREATE INDEX idx_pari_bet_actif ON listings_pari (bet_id, actif);
CREATE INDEX idx_pari_actif_resultat ON listings_pari (actif, resultat);
```

## Vérification post-migration

Après la migration, vérifiez que tout fonctionne :

```bash
# Tester les index
python manage.py dbshell
.schema creation_bdd_match
.schema listings_bet
.schema listings_pari

# Vérifier les types de champs
.schema listings_cote
```

## Notes importantes

- Les conversions FloatField → DecimalField peuvent nécessiter une migration des données
- Les index amélioreront significativement les performances des requêtes
- Testez sur un environnement de développement avant la production
