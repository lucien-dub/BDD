# models.py
from django.db import models

class RugbyMatch(models.Model):
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
    
    class Meta:
        verbose_name = "Match de rugby"
        verbose_name_plural = "Matchs de rugby"

# import_matches.py
import pandas as pd
from datetime import datetime
from django.db import transaction
from yourapp.models import RugbyMatch

def clean_poule_niveau(poule_string):
    """Extrait le niveau et la poule depuis la chaîne de caractères"""
    parts = poule_string.split('-')
    if len(parts) >= 2:
        niveau = parts[0].strip()
        return niveau, poule_string
    return poule_string, poule_string

def import_rugby_matches(file_path):
    # Lire le fichier
    df = pd.read_csv(file_path, delimiter=' ', header=0)
    
    try:
        with transaction.atomic():
            for index, row in df.iterrows():
                # Extraction de la date et l'heure
                date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", 
                                          format='%d/%m/%Y %H:%M')
                
                # Extraction du niveau et de la poule
                niveau, poule = clean_poule_niveau(row['Poule'])
                
                # Création du match
                match = RugbyMatch.objects.create(
                    date=date_heure.date(),
                    heure=date_heure.time(),
                    equipe1=row['Équipe 1'].strip(),
                    equipe2=row['Équipe 2'].strip(),
                    score1=int(row['Score 1']) if pd.notna(row['Score 1']) else 0,
                    score2=int(row['Score 2']) if pd.notna(row['Score 2']) else 0,
                    niveau=niveau,
                    poule=poule
                )
                print(f"Match importé: {match}")
                
    except Exception as e:
        print(f"Erreur lors de l'import: {str(e)}")

# Exemple d'utilisation
if __name__ == "__main__":
    file_path = 'Export_Resultats_20241117.csv'  # Assurez-vous que le fichier est au format CSV
    import_rugby_matches(file_path)