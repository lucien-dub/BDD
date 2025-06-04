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
        parser.add_argument('--delete-test-only', action='store_true', 
                           help='Supprimer UNIQUEMENT les matchs TEST_ avant création')
        parser.add_argument('--days-ahead', type=int, default=90, help='Nombre de jours dans le futur')
        parser.add_argument('--no-cotes', action='store_true', help='Ne pas créer de cotes')

    def handle(self, *args, **options):
        count = options['count']
        days_ahead = options['days_ahead']
        create_cotes = not options['no_cotes']
        
        # Sécurité: Ne supprimer QUE les matchs de test
        if options['delete_test_only']:
            test_matches = Match.objects.filter(equipe1__startswith='TEST_')
            if test_matches.exists():
                count_before = test_matches.count()
                test_matches.delete()
                self.stdout.write(self.style.WARNING(f'🔥 {count_before} matchs TEST_ supprimés'))
        
        # Vérification de sécurité
        total_real_matches = Match.objects.exclude(equipe1__startswith='TEST_').count()
        self.stdout.write(f'🛡️ Matchs réels protégés: {total_real_matches}')
        
        # Données pour génération
        villes = ['Lyon', 'Paris', 'Marseille', 'Toulouse', 'Bordeaux', 'Lille', 'Nantes', 'Strasbourg', 'Rennes']
        sports = ['Football', 'Basketball', 'Volleyball', 'Handball', 'Rugby']
        niveaux = ['M1', 'M2', 'L3', 'Master', 'Licence']
        academies = ['Lyon', 'Clermont', 'Grenoble', 'Saint Etienne', 'Montpellier']
        heures = ['14:00:00', '16:00:00', '18:00:00', '20:00:00']
        
        matches_created = 0
        cotes_created = 0
        created_matches = []  # Stocker les matchs créés
        
        self.stdout.write(f'🚀 Création de {count} matchs TEST...')
        
        # ÉTAPE 1: Créer tous les matchs SANS les cotes
        for i in range(count):
            try:
                sport = random.choice(sports)
                ville1 = random.choice(villes)
                ville2 = random.choice([v for v in villes if v != ville1])
                
                match = Match.objects.create(
                    sport=sport,
                    date=datetime.now().date() + timedelta(days=random.randint(1, days_ahead)),
                    heure=datetime.strptime(random.choice(heures), '%H:%M:%S').time(),
                    equipe1=f"TEST_{ville1}_{sport}_{i+1}",  # Ajouter un numéro unique
                    equipe2=f"TEST_{ville2}_{sport}_{i+1}",
                    score1=0,
                    score2=0,
                    niveau=random.choice(niveaux),
                    poule=f"{random.choice(['A', 'B', 'C'])}{random.randint(1, 3)}",
                    match_joue=False,
                    forfait_1=False,
                    forfait_2=False,
                    lieu=f"Stade {random.choice(villes)}",
                    arbitre="TEST_Arbitre",
                    commentaires="Match de test automatique",
                    academie=random.choice(academies)
                )
                
                matches_created += 1
                created_matches.append(match)
                self.stdout.write(f'✅ Match {i+1} créé (ID: {match.id})')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur création match {i+1}: {e}"))
                continue
        
        # ÉTAPE 2: Créer les cotes pour chaque match créé
        if create_cotes and matches_created > 0:
            self.stdout.write(f'\n🎯 Création des cotes pour {len(created_matches)} matchs...')
            
            for match in created_matches:
                try:
                    cote = Cote.objects.create(
                        match=match,
                        cote1=round(random.uniform(1.5, 3.5), 2),
                        coteN=round(random.uniform(2.8, 4.5), 2),
                        cote2=round(random.uniform(1.5, 3.5), 2)
                    )
                    cotes_created += 1
                    self.stdout.write(f'✅ Cote créée pour match {match.id}')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Erreur cote pour match {match.id}: {e}"))
                    continue
        
        # Résultats finaux
        self.stdout.write(self.style.SUCCESS(f'\n🎉 RÉSULTAT FINAL:'))
        self.stdout.write(self.style.SUCCESS(f'✅ {matches_created} matchs TEST créés'))
        if create_cotes:
            self.stdout.write(self.style.SUCCESS(f'✅ {cotes_created} cotes créées'))
        
        # Vérification finale
        final_real = Match.objects.exclude(equipe1__startswith='TEST_').count()
        final_test = Match.objects.filter(equipe1__startswith='TEST_').count()
        final_cotes = Cote.objects.filter(match__equipe1__startswith='TEST_').count()
        
        self.stdout.write(f'\n📊 État final:')
        self.stdout.write(f'   • Matchs réels: {final_real}')
        self.stdout.write(f'   • Matchs TEST: {final_test}')
        self.stdout.write(f'   • Cotes TEST: {final_cotes}')
        
        # Exemples
        if final_test > 0:
            self.stdout.write('\n📅 Exemples de matchs créés:')
            exemples = Match.objects.filter(equipe1__startswith='TEST_').order_by('-id')[:3]
            for match in exemples:
                try:
                    cote_obj = Cote.objects.filter(match=match).first()
                    if cote_obj:
                        cote_info = f" | Cotes: 1:{cote_obj.cote1} N:{cote_obj.coteN} 2:{cote_obj.cote2}"
                    else:
                        cote_info = " | Pas de cote"
                    self.stdout.write(f"  • {match.equipe1} vs {match.equipe2} ({match.date}){cote_info}")
                except Exception as e:
                    self.stdout.write(f"  • Erreur affichage match {match.id}: {e}")
