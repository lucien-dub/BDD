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
        parser.add_argument('--no-cotes', action='store_true', help='Ne pas créer de cotes (matchs seulement)')

    def handle(self, *args, **options):
        count = options['count']
        days_ahead = options['days_ahead']
        create_cotes = not options['no_cotes']
        
        if options['delete_first']:
            matches_deleted = Match.objects.filter(equipe1__startswith='TEST_').delete()
            self.stdout.write(f'Matchs fictifs supprimés: {matches_deleted[0]}')

        # Listes pour générer des données
        villes = [
            'Lyon', 'Paris', 'Marseille', 'Toulouse', 'Bordeaux', 
            'Lille', 'Nantes', 'Strasbourg', 'Montpellier', 'Rennes',
            'Nice', 'Saint-Étienne', 'Grenoble', 'Angers', 'Dijon'
        ]
        
        sports = ['Football', 'Basketball', 'Volleyball', 'Handball', 'Rugby']
        niveaux = ['M1', 'M2', 'L3', 'Master', 'Licence']
        academies = [
            'Lyon', 'Clermont', 'Grenoble', 'Saint Etienne', 'Aix/Marseille',
            'Montpellier', 'Toulouse', 'Angers', 'Bordeaux', 'Reims'
        ]
        heures_matches = ['14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']
        
        matches_created = 0
        cotes_created = 0
        
        self.stdout.write(f'🚀 Création de {count} matchs fictifs...')
        
        for i in range(count):
            # Utiliser une transaction pour chaque match + sa cote
            try:
                with transaction.atomic():
                    # Générer les données du match
                    sport = random.choice(sports)
                    academie = random.choice(academies)
                    niveau = random.choice(niveaux)
                    
                    ville1 = random.choice(villes)
                    ville2 = random.choice([v for v in villes if v != ville1])
                    
                    equipe1 = f"TEST_{ville1}_{sport}_{niveau}"
                    equipe2 = f"TEST_{ville2}_{sport}_{niveau}"
                    
                    date_match = datetime.now().date() + timedelta(days=random.randint(1, days_ahead))
                    heure_match = datetime.strptime(random.choice(heures_matches), '%H:%M').time()
                    
                    # Créer le match
                    match = Match(
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
                    match.save()  # Sauver d'abord le match
                    matches_created += 1
                    self.stdout.write(f'✅ Match {match.id} créé: {equipe1} vs {equipe2}')
                    
                    # Créer la cote si demandé
                    if create_cotes:
                        cote1 = round(random.uniform(1.2, 4.0), 2)
                        coteN = round(random.uniform(2.5, 5.0), 2)
                        cote2 = round(random.uniform(1.2, 4.0), 2)
                        
                        cote = Cote(
                            match=match,  # Le match est maintenant sauvé
                            cote1=cote1,
                            coteN=coteN,
                            cote2=cote2
                        )
                        cote.save()
                        cotes_created += 1
                        self.stdout.write(f'✅ Cote créée pour match {match.id}: 1:{cote1} N:{coteN} 2:{cote2}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur création match {i+1}: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
                continue
        
        # Résultats finaux
        self.stdout.write(self.style.SUCCESS(f'\n🎉 RÉSULTAT FINAL:'))
        self.stdout.write(self.style.SUCCESS(f'✅ {matches_created} matchs fictifs créés!'))
        if create_cotes:
            self.stdout.write(self.style.SUCCESS(f'✅ {cotes_created} cotes créées!'))
        
        # Afficher quelques exemples
        if matches_created > 0:
            self.stdout.write('\n📅 Derniers matchs créés:')
            exemples = Match.objects.filter(equipe1__startswith='TEST_').order_by('-id')[:5]
            for match in exemples:
                try:
                    cotes = Cote.objects.filter(match=match)
                    if cotes.exists():
                        cote = cotes.first()
                        cote_info = f" (Cotes: 1:{cote.cote1:.2f}, N:{cote.coteN:.2f}, 2:{cote.cote2:.2f})"
                    else:
                        cote_info = " (Pas de cote)"
                    self.stdout.write(f"  • ID:{match.id} - {match.date} {match.heure} - {match.equipe1} vs {match.equipe2}{cote_info}")
                except Exception as e:
                    self.stdout.write(f"  • ID:{match.id} - Erreur affichage: {e}")
        
        # Stats finales
        total_test_matches = Match.objects.filter(equipe1__startswith='TEST_').count()
        total_test_cotes = Cote.objects.filter(match__equipe1__startswith='TEST_').count()
        self.stdout.write(f'\n📊 Total dans la base:')
        self.stdout.write(f'   • Matchs de test: {total_test_matches}')
        self.stdout.write(f'   • Cotes de test: {total_test_cotes}')
