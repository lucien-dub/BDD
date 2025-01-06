from django.db import models
import pandas as pd
from datetime import datetime
from django.db import transaction
import re
from django.core.validators import MinValueValidator
from listings.models import Match, Cote

def extraire_sport(texte):
    match = re.search(r'-\s*(.*?)\s*\(', texte)
    return match.group(1).strip() if match else ''

def extraire_niveau(texte):
    match = re.search(r'\((.*?)\)', texte)
    return match.group(1).strip() if match else ''

def extraire_poule(texte):
    match = re.search(r'(\w{2})(?= -)',texte)
    return match.group(1).strip() if match else ''

def import_matches(file_path):
    # Lire le fichier
    df = pd.read_excel(file_path, engine='openpyxl')
    matches_crees = []
    
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                # Extraction de la date et l'heure
                date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", 
                                          format='%d/%m/%Y %H:%M')
                
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
                matches_crees.append(match)
                print(f"Match importé: {match}")
            
            # Affecter les cotes après avoir créé tous les matches
            affectation_cote(matches_crees)
                
    except Exception as e:
        print(f"Erreur lors de l'import: {str(e)}")

def calculer_cote(match):
    """Calcul de la cote pour le match."""
    return round(1 / (1.01 + match.id), 2)

def affectation_cote(matches):
    """Ajoute des cotes pour chaque match en utilisant bulk_create."""
    cotes_a_creer = []
    
    for match in matches:
        cotes_a_creer.extend([
            Cote(match=match, type_cote=f"victoire {match.equipe1}", valeur=calculer_cote(match)),
            Cote(match=match, type_cote=f"victoire {match.equipe2}", valeur=1 + calculer_cote(match)),
            Cote(match=match, type_cote="Nul", valeur=2 + calculer_cote(match))
        ])
    
    Cote.objects.bulk_create(cotes_a_creer)

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'merchex.settings')
    django.setup()
    
    file_path = 'Export_Resultats_20241117.xlsx'
    import_matches(file_path)