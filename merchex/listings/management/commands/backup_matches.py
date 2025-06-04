# listings/management/commands/backup_matches.py
from django.core.management.base import BaseCommand
from listings.models import Match, Cote
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Sauvegarde tous les matchs réels en JSON'

    def handle(self, *args, **options):
        # Sauvegarder seulement les vrais matchs (pas les TEST_)
        real_matches = Match.objects.exclude(equipe1__startswith='TEST_')
        
        backup_data = []
        for match in real_matches:
            match_data = {
                'id': match.id,
                'sport': match.sport,
                'date': str(match.date),
                'heure': str(match.heure),
                'equipe1': match.equipe1,
                'equipe2': match.equipe2,
                'score1':int(match.score1),
                'score2':int(match.score2),
                'niveau': match.niveau,
                'poule': match.poule,
                'match_joue': match.match_joue,
                'forfait_1': match.forfait_1,
                'forfait_2': match.forfait_2,
                'lieu': match.lieu,
                'academie': match.academie
            }
            
            # Ajouter les cotes 
            cotes = Cote.objects.filter(match=match)
            if cotes.exists():
                cote = cotes.first()
                match_data['cotes'] = {
                    'cote1': float(cote.cote1),
                    'coteN': float(cote.coteN),
                    'cote2': float(cote.cote2)
                }
            
            backup_data.append(match_data)
        
        # Sauvegarder
        filename = f"backup_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'✅ {len(backup_data)} matchs sauvés dans {filename}')
