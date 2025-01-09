from django.db.models import Avg, Count
from datetime import datetime, timedelta
import math

def calculer_cotes(match_id):
    """
    Calcule les cotes pour un match donné en se basant sur:
    - Historique des résultats récents
    - Niveau des équipes
    - Performance dans la poule
    """
    try:
        match = Match.objects.get(id=match_id)
        date_limite = match.date - timedelta(days=365)
        
        # Récupérer l'historique des matches pour les deux équipes
        historique = Match.objects.filter(
            date__gte=date_limite,
            date__lt=match.date,
            sport=match.sport,
            niveau=match.niveau
        )
        
        # Statistiques équipe 1
        stats_eq1 = historique.filter(equipe1=match.equipe1)
        victoires_eq1 = stats_eq1.filter(score1__gt='score2').count()
        matches_eq1 = stats_eq1.count()
        
        # Statistiques équipe 2
        stats_eq2 = historique.filter(equipe1=match.equipe2)
        victoires_eq2 = stats_eq2.filter(score1__gt='score2').count()
        matches_eq2 = stats_eq2.count()
        
        # Calcul des probabilités de base
        if matches_eq1 > 0 and matches_eq2 > 0:
            prob_eq1 = victoires_eq1 / matches_eq1
            prob_eq2 = victoires_eq2 / matches_eq2
            prob_nul = 1 - (prob_eq1 + prob_eq2)
            
            # Ajustement pour garantir des probabilités valides
            total_prob = prob_eq1 + prob_eq2 + prob_nul
            prob_eq1 /= total_prob
            prob_eq2 /= total_prob
            prob_nul /= total_prob
            
            # Conversion en cotes (avec une marge de 10%)
            marge = 1.1
            cote1 = round(marge / prob_eq1, 2) if prob_eq1 > 0 else 3.0
            cote2 = round(marge / prob_eq2, 2) if prob_eq2 > 0 else 3.0
            coteN = round(marge / prob_nul, 2) if prob_nul > 0 else 3.0
        else:
            # Cotes par défaut si pas assez d'historique
            cote1 = cote2 = 2.5
            coteN = 3.0
        
        # Création ou mise à jour des cotes
        Cote.objects.update_or_create(
            match=match,
            defaults={
                'cote1': cote1,
                'cote2': cote2,
                'coteN': coteN
            }
        )
        
        return cote1, coteN, cote2
        
    except Match.DoesNotExist:
        raise ValueError(f"Match avec ID {match_id} non trouvé")