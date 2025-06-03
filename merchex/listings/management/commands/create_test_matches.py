# listings/management/commands/create_test_matches.py
from django.core.management.base import BaseCommand
from django.db import transaction
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
            # Supprimer les matchs fictifs existants (et leurs cotes associées)
            matches_deleted = Match.objects.filter(equipe1__startswith='TEST_').delete()
            self.stdout.write(f'Matchs fictifs supprimés: {matches_deleted[0]}')

        # Listes pour générer des noms d'équipes réalistes
        villes = [
            'Lyon', 'Paris', 'Marseille', 'Toulouse', 'Bordeaux', 
            'Lille', 'Nantes', 'Strasbourg', 'Montpellier', 'Rennes',
            'Nice', 'Saint-Étienne', 'Grenoble', 'Angers', 'Dijon',
            'Clermont', 'Amiens', 'Besançon', 'Caen', 'Limoges'
        ]
        
        sports = ['Football', 'Basketball', 'Volleyball', 'Handball', 'Rugby', 'Tennis']
        niveaux = ['M1', 'M2', 'L3', 'Master', 'Licence']
        
        # Académies existantes dans ton système
        academies = [
            'Lyon', 'Clermont', 'Grenoble', 'Saint Etienne', 'Aix/Marseille',
            'Montpellier', 'Toulouse', 'Angers', 'Bordeaux', 'Reims',
            'Ile-de-France', 'Strasbourg'
        ]
        
        # Heures de match réalistes
        heures_matches = ['14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']
        
        matches_created = 0
        cotes_created = 0
        
        self.stdout.write(f'🚀 Création de {count} matchs fictifs...')
        
        for i in range(count):
            try:
                with transaction.atomic():
                    # Générer des données aléatoires mais réalistes
                    sport = random.choice(sports)
                    academie = random.choice(academies)
                    niveau = random.choice(niveaux)
                    
                    # Générer des noms d'équipes avec préfixe TEST_
                    ville1 = random.choice(villes)
                    ville2 = random.choice([v for v in villes if v != ville1])
                    
                    equipe1 = f"TEST_{ville1}_{sport}_{niveau}"
                    equipe2 = f"TEST_{ville2}_{sport}_{niveau}"
                    
                    # Date future aléatoire
                    date_match = datetime.now().date() + timedelta(days=random.randint(1, days_ahead))
                    heure_match = datetime.strptime(random.choice(heures_matches), '%H:%M').time()
                    
                    # ÉTAPE 1: Créer et sauvegarder le match D'ABORD
                    match = Match.objects.create(
                        sport=sport,
                        date=date_match,
                        heure=heure_match,
                        equipe1=equipe1,
                        equipe2=equipe2,
                        score1=0,
                        score2=0,
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
                    
                    # Le match est maintenant sauvé en base avec un ID valide
                    matches_created += 1
                    self.stdout.write(f'✅ Match {match.id} créé: {equipe1} vs {equipe2}')
                    
                    # ÉTAPE 2: Maintenant créer la cote (le match existe en base)
                    cote1 = round(random.uniform(1.2, 4.0), 2)
                    coteN = round(random.uniform(2.5, 5.0), 2)
                    cote2 = round(random.uniform(1.2, 4.0), 2)
                    
                    # Maintenant on peut créer la cote car match.id existe
                    cote = Cote.objects.create(
                        match=match,  # match est maintenant sauvé avec un ID valide
                        cote1=cote1,
                        coteN=coteN,
                        cote2=cote2
                    )
                    
                    cotes_created += 1
                    self.stdout.write(f'  → Cote créée pour le match {match.id}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur création match {i+1}: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 RÉSULTAT FINAL:'))
        self.stdout.write(self.style.SUCCESS(f'✅ {matches_created} matchs fictifs créés avec succès!'))
        self.stdout.write(self.style.SUCCESS(f'✅ {cotes_created} cotes créées avec succès!'))
        
        # Afficher quelques exemples
        if matches_created > 0:
            self.stdout.write('\n📅 Exemples de matchs créés:')
            exemples = Match.objects.filter(equipe1__startswith='TEST_').order_by('-id')[:5]
            for match in exemples:
                try:
                    cote = Cote.objects.filter(match=match).first()
                    if cote:
                        cote_info = f" (Cotes: 1:{cote.cote1:.2f}, N:{cote.coteN:.2f}, 2:{cote.cote2:.2f})"
                    else:
                        cote_info = " (Pas de cote)"
                    self.stdout.write(f"  • ID:{match.id} - {match.date} {match.heure} - {match.equipe1} vs {match.equipe2}{cote_info}")
                except Exception as e:
                    self.stdout.write(f"  • ID:{match.id} - {match.date} {match.heure} - {match.equipe1} vs {match.equipe2} (Erreur affichage)")
        
        # Statistiques finales
        total_test_matches = Match.objects.filter(equipe1__startswith='TEST_').count()
        self.stdout.write(f'\n📊 Total matchs de test dans la base: {total_test_matches}')
