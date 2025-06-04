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
        # SUPPRESSION DE L'OPTION DANGEREUSE --delete-first

    def handle(self, *args, **options):
        count = options['count']
        days_ahead = options['days_ahead']
        create_cotes = not options['no_cotes']
        
        # ⚠️ SÉCURITÉ: Ne supprimer QUE les matchs de test
        if options['delete_test_only']:
            test_matches = Match.objects.filter(equipe1__startswith='TEST_')
            if test_matches.exists():
                count_before = test_matches.count()
                test_matches.delete()
                self.stdout.write(self.style.WARNING(f'🔥 {count_before} matchs TEST_ supprimés'))
            else:
                self.stdout.write('ℹ️ Aucun match TEST_ à supprimer')
        
        # Vérification de sécurité
        total_real_matches = Match.objects.exclude(equipe1__startswith='TEST_').count()
        self.stdout.write(f'🛡️ Matchs réels protégés: {total_real_matches}')

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
            try:
                with transaction.atomic():
                    # Créer le match de test
                    sport = random.choice(sports)
                    ville1 = random.choice(villes)
                    ville2 = random.choice([v for v in villes if v != ville1])
                    
                    match = Match(
                        sport=sport,
                        date=datetime.now().date() + timedelta(days=random.randint(1, days_ahead)),
                        heure=datetime.strptime(random.choice(['14:00', '16:00', '18:00']), '%H:%M').time(),
                        equipe1=f"TEST_{ville1}_{sport}",
                        equipe2=f"TEST_{ville2}_{sport}",
                        score1=0,
                        score2=0,
                        niveau=random.choice(['M1', 'M2', 'L3']),
                        poule=f"{random.choice(['A', 'B', 'C'])}1",
                        match_joue=False,
                        forfait_1=False,
                        forfait_2=False,
                        lieu=f"Stade {random.choice(villes)}",
                        arbitre="TEST_Arbitre",
                        commentaires="Match de test automatique",
                        academie=random.choice(['Lyon', 'Clermont', 'Grenoble'])
                    )
                    match.save()
                    matches_created += 1
                    
                    if create_cotes:
                        cote = Cote(
                            match=match,
                            cote1=round(random.uniform(1.5, 3.5), 2),
                            coteN=round(random.uniform(2.8, 4.5), 2),
                            cote2=round(random.uniform(1.5, 3.5), 2)
                        )
                        cote.save()
                        cotes_created += 1
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur match {i+1}: {e}"))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {matches_created} matchs TEST créés'))
        self.stdout.write(self.style.SUCCESS(f'✅ {cotes_created} cotes créées'))
        
        # Stats finales
        final_real = Match.objects.exclude(equipe1__startswith='TEST_').count()
        final_test = Match.objects.filter(equipe1__startswith='TEST_').count()
        self.stdout.write(f'\n📊 État final:')
        self.stdout.write(f'   • Matchs réels: {final_real}')
        self.stdout.write(f'   • Matchs TEST: {final_test}')