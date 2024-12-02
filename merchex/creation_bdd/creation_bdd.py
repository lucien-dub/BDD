# models.py
from django.db import models
import pandas as pd
from datetime import datetime
from django.db import transaction
import re
from django.core.validators import MinValueValidator
from django.apps import apps
from listings.models import Match, Cote

current_id = 0

def get_next_id():
    global current_id
    current_id += 1
    return current_id

# extraction des différentes données dans la chaine de caractère avec regex
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
    df = pd.read_excel(file_path, engine = 'openpyxl')

    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                # Extraction de la date et l'heure
                date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", 
                                          format='%d/%m/%Y %H:%M')
                
                # Création du match
                match = Match.objects.create(
                    id = get_next_id(),
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
                print(f"Match importé: {match}")
                
    except Exception as e:
        print(f"Erreur lors de l'import: {str(e)}")


#Calcul de la côte
def calculer_cote(Match):
    """Calcul de la cote pour le match (ici la formule est abérrante juste pour pouvoir avancer dans le projet)"""
    return round(1 / (1.01+Match.id), 2)  # Formule basique : 1 / id

def affectation_cote(Match):
    for Match in Match.objects.all():
        Cote.objects.create(match=Match, type_cote=f"victoire {Match.equipe1}", valeur=calculer_cote(Match.id))
        Cote.objects.create(match=Match, type_cote=f"victoire {Match.equipe2}", valeur=1+ calculer_cote(Match.id))
        Cote.objects.create(match=Match, type_cote="Nul", valeur=2 + calculer_cote(Match.id))

# Exemple d'utilisation
if __name__ == "__main__":
    file_path = 'Export_Resultats_20241117.csv'  # Assurez-vous que le fichier est au format CSV
    import_matches(file_path)