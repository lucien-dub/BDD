from django.db.models import Avg, Count, F
from datetime import datetime, timedelta
from django.utils import timezone
import math
from listings.models import Match, Cote, Pari

def calculer_cotes(match_id):
    """
    Calcule les cotes pour un match donné basé sur l'historique
    """
    try:
        match = Match.objects.get(id=match_id)
        date_limite = match.date - timedelta(days=365)
        
        historique = Match.objects.filter(
            date__gte=date_limite,
            date__lt=match.date,
            sport=match.sport,
            niveau=match.niveau
        )
        
        pari = Pari.objects.get(match.id ==match_id)

        if pari != []:
            v1 = 0
            v2 = 0
            vN = 0
            for p in pari:
                sel = p.match.selection
                if sel == '1':
                    v1 += 1
                elif sel == '2':
                    v2 += 1
                elif sel == 'N':
                    vN += 1

        vtot = v1 + v2 + vN

        # Statistiques équipe 1
        stats_eq1 = historique.filter(equipe1=match.equipe1)
        victoires_eq1 = stats_eq1.filter(score1__gt=F('score2')).count()
        matches_eq1 = stats_eq1.count()
        
        # Statistiques équipe 2
        stats_eq2 = historique.filter(equipe1=match.equipe2)
        victoires_eq2 = stats_eq2.filter(score1__gt=F('score2')).count()
        matches_eq2 = stats_eq2.count()
        
        # Calcul des probabilités
        if matches_eq1 > 0 and matches_eq2 > 0:
            prob_eq1 = victoires_eq1 / matches_eq1 + v1/vtot
            prob_eq2 = victoires_eq2 / matches_eq2 + v2/vtot
            prob_nul = 1 - (prob_eq1 + prob_eq2) + vN/vtot
            
            total_prob = prob_eq1 + prob_eq2 + prob_nul
            if total_prob > 0:
                prob_eq1 /= total_prob
                prob_eq2 /= total_prob
                prob_nul /= total_prob
            
            # Conversion en cotes (marge 10%)
            marge = 1.1
            cote1 = round(marge / max(prob_eq1, 0.1), 2)
            cote2 = round(marge / max(prob_eq2, 0.1), 2)
            coteN = round(marge / max(prob_nul, 0.1), 2)
        else:
            # Cotes par défaut
            cote1 = cote2 = 2.5
            coteN = 3.0


        # Mise à jour ou création
        cote, created = Cote.objects.update_or_create(
            match=match,
            defaults={
                'cote1': cote1,
                'cote2': cote2,
                'coteN': coteN
            }
        )
        
        return cote.cote1, cote.coteN, cote.cote2
        
    except Match.DoesNotExist:
        raise ValueError(f"Match avec ID {match_id} non trouvé")