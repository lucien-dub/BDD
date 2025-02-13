from django.core.management.base import BaseCommand
from listings.models import Match, Cote
from django.db.models import F
from datetime import timedelta

class Command(BaseCommand):
    help = 'Calcule les cotes pour les matchs basés sur l\'historique'

    def handle(self, *args, **kwargs):
        self.stdout.write('Début du calcul des cotes pour les matchs...')

        try:
            matches = Match.objects.all()
            for match in matches:
                self.calculer_cotes(match.id)
            self.stdout.write(self.style.SUCCESS('Calcul des cotes terminé avec succès !'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors du calcul des cotes : {str(e)}'))

    def calculer_cotes(self, match_id):
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
                prob_eq1 = victoires_eq1 / matches_eq1
                prob_eq2 = victoires_eq2 / matches_eq2
                prob_nul = 1 - (prob_eq1 + prob_eq2)

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

            self.stdout.write(self.style.SUCCESS(f'Cotes calculées pour le match {match.id}: cote1={cote1}, coteN={coteN}, cote2={cote2}'))

        except Match.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Match avec ID {match_id} non trouvé"))
