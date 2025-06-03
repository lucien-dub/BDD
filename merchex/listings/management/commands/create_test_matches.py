# listings/management/commands/create_test_matches.py
from django.core.management.base import BaseCommand
from listings.models import Match, Cote
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Crée des matchs fictifs pour tester l\'application'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=30, help='Nombre de matchs à créer')
        parser.add_argument('--delete-first', action='store_true', help='Supprimer les matchs fictifs existants avant')
        parser.add_argument('--days-ahead', type=int, default=90, help='Nombre de jours dans le futur pour les matchs')

    def handle(self, *args, **options):
        count = options['count']
        days_ahead = options['days_ahead']
        
        if options['delete_first']:
            # Supprimer les matchs fictifs existants
            deleted = Match.objects.filter(equipe1__startswith='TEST_').delete()
            self.stdout.write(f'Matchs fictifs supprimés: {deleted[0]}')

        # Listes pour générer des noms d'équipes réalistes
        villes = [
            'Lyon', 'Paris', 'Marseille', 'Toulouse', 'Bordeaux', 
            'Lille', 'Nantes', 'Strasbourg', 'Montpellier', 'Rennes',
            'Nice', 'Saint-Étienne', 'Grenoble', 'Angers', 'Dijon',
            'Clermont', 'Amiens', 'Besançon', 'Caen', 'Limoges',
            'Nancy', 'Orléans', 'Poitiers', 'Reims', 'Rouen'
        ]
        
        sports = ['Football', 'Basketball', 'Volleyball', 'Handball', 'Rugby', 'Tennis']
        niveaux = ['M1', 'M2', 'L3', 'Master', 'Licence']
        
        # Académies existantes dans ton système
        academies = [
            'Aix-Marseille', 'Amiens', 'Besançon', 'Bordeaux', 'Caen',
            'Clermont-Ferrand', 'Créteil', 'Dijon', 'Grenoble', 'Lille',
            'Limoges', 'Lyon', 'Montpellier', 'Nancy-Metz', 'Nantes',
            'Nice', 'Orléans-Tours', 'Paris', 'Poitiers', 'Reims',
            'Rennes', 'Rouen', 'Strasbourg', 'Toulouse', 'Versailles'
        ]
        
        # Heures de match réalistes
        heures_matches = ['14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00']
        
        matches_created = 0
        next_id = self.get_next_available_id()
        
        for i in range(count):
            try:
                # Générer des données aléatoires
                sport = random.choice(sports)
                niveau = random.choice(niveaux)
                academie = random.choice(academies)
                
                # Créer des noms d'équipe uniques avec préfixe TEST_
                ville1 = random.choice(villes)
                ville2 = random.choice(villes)
                
                # S'assurer que les villes sont différentes
                while ville1 == ville2:
                    ville2 = random.choice(villes)
                
                equipe1 = f"TEST_{ville1} {sport} {niveau}"
                equipe2 = f"TEST_{ville2} {sport} {niveau}"
                
                # Dates futures (entre aujourd'hui et dans X jours)
                date_match = datetime.now().date() + timedelta(days=random.randint(1, days_ahead))
                heure_match = random.choice(heures_matches)
                
                # Convertir l'heure en objet time
                heure_obj = datetime.strptime(heure_match, '%H:%M').time()
                
                lieu = f"Campus {ville1} - Complexe Sportif {random.randint(1, 5)}"
                poule = random.choice(['A', 'B', 'C', 'D']) + str(random.randint(1, 4))
                
                # Créer le match avec scores à 0 (match à venir)
                match = Match(
                    id=next_id + i,  # ID unique
                    equipe1=equipe1,
                    equipe2=equipe2,
                    date=date_match,
                    heure=heure_obj,
                    sport=sport,
                    niveau=niveau,
                    lieu=lieu,
                    poule=poule,
                    academie=academie,
                    score1=0,  # Match à venir
                    score2=0,  # Match à venir
                    match_joue=False,
                    forfait_1=False,
                    forfait_2=False,
                    arbitre=f"Arbitre {random.randint(1, 50)}",
                    commentaires=f"Match de test généré automatiquement - {sport} {niveau}"
                )
                match.save()
                
                # Créer les cotes pour ce match
                cote = Cote(
                    match=match,
                    cote1=round(random.uniform(1.5, 3.5), 2),
                    coteN=round(random.uniform(2.8, 4.5), 2),
                    cote2=round(random.uniform(1.5, 3.5), 2)
                )
                cote.save()
                
                matches_created += 1
                
                if matches_created % 10 == 0:
                    self.stdout.write(f'{matches_created} matchs créés...')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur lors de la création du match {i+1}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {matches_created} matchs fictifs créés avec succès!')
        )
        
        # Afficher quelques exemples
        sample_matches = Match.objects.filter(equipe1__startswith='TEST_').order_by('date')[:5]
        self.stdout.write('\n📅 Exemples de matchs créés:')
        for match in sample_matches:
            cote = match.cotes.first()
            cotes_info = f" (Cotes: 1:{cote.cote1} N:{cote.coteN} 2:{cote.cote2})" if cote else ""
            self.stdout.write(f'   • {match.equipe1} vs {match.equipe2}')
            self.stdout.write(f'     📍 {match.lieu} - {match.date} à {match.heure}{cotes_info}')
            self.stdout.write('')

    def get_next_available_id(self):
        """Trouve le prochain ID disponible pour les matchs"""
        last_match = Match.objects.all().order_by('-id').first()
        if last_match:
            return last_match.id + 1
        return 1
