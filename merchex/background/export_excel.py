import pandas as pd
import requests
from django.db import transaction
from listings.models import Match, Cote
import re
from datetime import datetime

def export_excel_website(url: str, df_original, name_file: str):
    """
    Fonction permettant d'aller faire une requete POST pour exporter le fichier excel planning sur le site de la FFSU
    """
    try:
        response = requests.post(url)
        if response.status_code == 200:
            with open(name_file, 'wb') as file:
                file.write(response.content)
            print("File downloaded successfully!")
            
            df_new = pd.read_excel(name_file, engine='openpyxl')
            
            if df_original.equals(pd.DataFrame(df_new)):
                print("Les fichiers sont identiques.")
                return df_original, False
            else:
                print("Les fichiers sont différents.")
                return pd.DataFrame(df_new), True
                
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return df_original, False
            
    except Exception as e:
        print(f"Erreur lors de l'export: {str(e)}")
        return df_original, False

def import_matches_from_url(url, current_df=None):
    """
    Fonction principale qui gère l'export et l'import des matchs
    """
    if current_df is None:
        current_df = pd.DataFrame()  # DataFrame vide au début
        
    name_file = 'Export_Resultats.xlsx'
    df, changed = export_excel_website(url, current_df, name_file)
    
    if changed:
        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    # Vérifier si le match existe déjà
                    date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", 
                                              format='%d/%m/%Y %H:%M')
                    
                    match, created = Match.objects.update_or_create(
                        sport=extraire_sport(row['Poule']),
                        date=date_heure.date(),
                        heure=date_heure.time(),
                        equipe1=row['Équipe 1'].strip(),
                        equipe2=row['Équipe 2'].strip(),
                        defaults={
                            'score1': int(row['Score 1']) if pd.notna(row['Score 1']) else 0,
                            'score2': int(row['Score 2']) if pd.notna(row['Score 2']) else 0,
                            'niveau': extraire_niveau(row['Poule']),
                            'poule': extraire_poule(row['Poule'])
                        }
                    )
                    
                    if created:
                        print(f"Nouveau match créé: {match}")
                        # Créer les cotes pour le nouveau match
                        creer_cotes_pour_match(match)
                    else:
                        print(f"Match mis à jour: {match}")
                        
        except Exception as e:
            print(f"Erreur lors de l'import: {str(e)}")
            return current_df
            
        return df
    return current_df

def creer_cotes_pour_match(match):
    """Crée les cotes pour un match spécifique"""
    cotes = [
        Cote(match=match, type_cote=f"victoire {match.equipe1}", 
             valeur=calculer_cote(match)),
        Cote(match=match, type_cote=f"victoire {match.equipe2}", 
             valeur=1 + calculer_cote(match)),
        Cote(match=match, type_cote="Nul", 
             valeur=2 + calculer_cote(match))
    ]
    Cote.objects.bulk_create(cotes)

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'merchex.settings')
    django.setup()
    
    url = 'http://sportco.abyss-clients.com/rencontres/resultats/export'
    current_df = pd.DataFrame()  # DataFrame initial vide
    
    # Premier import
    current_df = import_matches_from_url(url, current_df)