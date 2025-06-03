# listings/management/commands/create_test_matches.py
from django.core.management.base import BaseCommand
from listings.models import Match, Cote
from datetime import datetime, timedelta
import random
from django.db import models

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
            # Supprimer les matchs fictifs existants (et leurs cotes associées)
            matches_deleted = Match.objects.filter(equipe1__startswith='TEST_').delete()
            self.stdout.write(f'Matchs fictifs supprimés: {matches_deleted[0]}')

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
            'Lyon', 'Clermont', 'Grenoble', 'Saint Etienne', 'Aix/Marseille',
            'Montpellier', 'Toulouse', 'Angers', 'La Roche-sur-Yon', 'Bordeaux',
            'Hauts-de-France', 'Reims', 'Ile-de-France', 'Strasbourg'
        ]
        
        # Heures de match réalistes
        heures_matches = ['14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00']
        
        matches_created = 0
        cotes_created = 0
        next_id = self.get_next_available_id()
        
        for i in range(count):
            try:
                # Générer des données aléatoires mais réalistes
                sport = random.choice(sports)
                academie = random.choice(academies)
                niveau = random.choice(niveaux)
                
                # Générer des noms d'équipes avec préfixe TEST_
                ville1 = random.choice(villes)
                ville2 = random.choice([v for v in villes if v != ville1])
                
                equipe1 = f"TEST_{ville1} {sport} {niveau}"
                equipe2 = f"TEST_{ville2} {sport} {niveau}"
                
                # Date future aléatoire
                date_match = datetime.now().date() + timedelta(days=random.randint(1, days_ahead))
                heure_match = datetime.strptime(random.choice(heures_matches), '%H:%M').time()
                
                # Créer le match individuellement (pas en bulk_create)
                match = Match.objects.create(
                    id=next_id,
                    sport=sport,
                    date=date_match,
                    heure=heure_match,
                    equipe1=equipe1,
                    equipe2=equipe2,
                    score1=0,  # Match non joué
                    score2=0,  # Match non joué
                    niveau=niveau,
                    poule=f"{random.choice(['A', 'B', 'C', 'D'])}1",
                    match_joue=False,
                    forfait_1=False,
                    forfait_2=False,
                    lieu=f"Stade {random.choice(villes)}",
                    arbitre="TEST_Arbitre",
                    commentaires="Match de test pour développement",
                    academie=academie
                )
                
                # Créer les cotes pour ce match
                self.creer_cotes_pour_match(match)
                
                matches_created += 1
                cotes_created += 1
                next_id += 1
                
            except Exception as e:
                self.stdout.write(f"Erreur lors de la création du match {i+1}: {str(e)}")
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✅ {matches_created} matchs fictifs créés avec succès!'))
        self.stdout.write(self.style.SUCCESS(f'✅ {cotes_created} cotes créées avec succès!'))
        
        # Afficher quelques exemples
        self.stdout.write('\n📅 Exemples de matchs créés:')
        exemples = Match.objects.filter(equipe1__startswith='TEST_').order_by('date')[:5]
        for match in exemples:
            cote = Cote.objects.filter(match=match).first()
            cote_info = f" (Cotes: 1:{cote.cote1:.2f}, N:{cote.coteN:.2f}, 2:{cote.cote2:.2f})" if cote else ""
            self.stdout.write(f"  • {match.date} {match.heure} - {match.equipe1} vs {match.equipe2}{cote_info}")

    def get_next_available_id(self):
        """Trouve le prochain ID disponible"""
        try:
            max_id = Match.objects.all().aggregate(max_id=models.Max('id'))['max_id']
            return (max_id + 1) if max_id else 1
        except:
            return 1

    def creer_cotes_pour_match(self, match):
        """Crée des cotes réalistes pour un match"""
        try:
            # Générer des cotes aléatoires mais réalistes
            # Cote pour victoire équipe 1 (entre 1.2 et 4.0)
            cote1 = round(random.uniform(1.2, 4.0), 2)
            
            # Cote pour match nul (entre 2.5 et 5.0)
            coteN = round(random.uniform(2.5, 5.0), 2)
            
            # Cote pour victoire équipe 2 (calculée pour équilibrer)
            cote2 = round(random.uniform(1.2, 4.0), 2)
            
            # S'assurer que les cotes sont cohérentes (ajuster si nécessaire)
            if cote1 < 1.1:
                cote1 = 1.1
            if cote2 < 1.1:
                cote2 = 1.1
            if coteN < 2.0:
                coteN = 2.0
            
            cote = Cote.objects.create(
                match=match,
                cote1=cote1,
                coteN=coteN,
                cote2=cote2
            )
            
            return cote
            
        except Exception as e:
            raise Exception(f"Erreur création cote pour match {match.id}: {str(e)}")
