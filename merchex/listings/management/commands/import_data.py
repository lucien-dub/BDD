import pandas as pd
from django.db import transaction
from listings.models import Match, Cote
import re
from django.core.management.base import BaseCommand
import os

def extraire_sport(texte):
    match = re.search(r'-\s*(.*?)\s*\(', texte)
    return match.group(1).strip() if match else ''

def extraire_niveau(texte):
    match = re.search(r'\((.*?)\)', texte)
    return match.group(1).strip() if match else ''

def extraire_poule(texte):
    match = re.search(r'(\w{2})(?= -)', texte)
    return match.group(1).strip() if match else ''

def import_matches(file_path):
    df = pd.read_excel(file_path, engine='openpyxl')

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Extraction et validation de la date
                    date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", format='%d/%m/%Y %H:%M')

                    if date_heure.year < 2020:
                        print(f"⚠️ Match ignoré : date trop ancienne ({date_heure})")
                        continue  # Passe au match suivant
                    
                    # Création du match
                    match = Match.objects.create(
                        sport=extraire_sport(row['Poule']),
                        date=date_heure.date(),
                        heure=date_heure.time(),
                        equipe1=row['Équipe 1'].strip(),
                        equipe2=row['Équipe 2'].strip(),
                        score1=int(row['Score 1']) if pd.notna(row['Score 1']) else 0,
                        score2=int(row['Score 2']) if pd.notna(row['Score 2']) else 0,
                        niveau=extraire_niveau(row['Poule']),
                        poule=extraire_poule(row['Poule'])
                    )
                    print(f"✅ Match importé: {match}")

                except Exception as e:
                    print(f"❌ Erreur sur la ligne {index + 1} : {e}")
                    continue  # Passe au match suivant

    except Exception as e:
        print(f"🚨 Erreur lors de l'import: {e}")

def calculer_cote(match):
    """Calcul de la cote pour le match."""
    return round(1 / (1.01 + match.id), 2)

def affectation_cote(matches):
    """Ajoute des cotes pour chaque match en utilisant bulk_create."""
    cotes_a_creer = []
    
    for match in matches:
        # Créer les trois types de cotes pour chaque match
        cotes_a_creer.extend([
            Cote(match=match, type_cote=f"victoire {match.equipe1}", valeur=calculer_cote(match)),
            Cote(match=match, type_cote=f"victoire {match.equipe2}", valeur=1 + calculer_cote(match)),
            Cote(match=match, type_cote="Nul", valeur=2 + calculer_cote(match))
        ])
    
    # Utiliser bulk_create pour insérer tous les objets en une seule requête
    Cote.objects.bulk_create(cotes_a_creer)


# Exemple d'utilisation
if __name__ == "__main__":
    file_path = 'Export_Resultats.csv'  # Assurez-vous que le fichier est au format CSV
    import_matches(file_path)

class Command(BaseCommand):
    help = 'Importe les matches depuis un fichier Excel'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Chemin vers le fichier Excel')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Le fichier {file_path} n\'existe pas'))
            return

        # Importer les matches
        try:
            import_matches(file_path)
            
            # Affecter les cotes aux matches importés
            matches = Match.objects.all()
            affectation_cote(matches)
            
            self.stdout.write(self.style.SUCCESS('Import réussi'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de l\'import: {str(e)}'))