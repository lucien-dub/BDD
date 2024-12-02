# models.py
from django.db import models
import pandas as pd
from datetime import datetime
from django.db import transaction
import re

current_id = 0

def get_next_id():
    global current_id
    current_id += 1
    return current_id

class Match(models.Model):
    id = models.IntegerField(primary_key=True)
    sport = models.CharField(max_length=50)
    date = models.DateField()
    heure = models.TimeField()
    equipe1 = models.CharField(max_length=100)
    equipe2 = models.CharField(max_length=100)
    score1 = models.IntegerField()
    score2 = models.IntegerField()
    niveau = models.CharField(max_length=50)
    poule = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.equipe1} vs {self.equipe2} - {self.date}"

class Cote(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="cotes")
    type_cote = models.CharField(max_length=50)  # Par exemple, "victoire", "nul", etc.
    valeur = models.FloatField()

    def __str__(self):
        return f"Cote {self.type_cote} pour {self.match}: {self.valeur}"



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
    df = pd.read_csv(file_path, delimiter=' ', header=0)

    
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

# Exemple d'utilisation
if __name__ == "__main__":
    file_path = 'Export_Resultats_20241117.csv'  # Assurez-vous que le fichier est au format CSV
    import_matches(file_path)