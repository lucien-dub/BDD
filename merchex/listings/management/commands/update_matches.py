from django.core.management.base import BaseCommand
import pandas as pd
import requests
from django.db import transaction
from listings.models import Match, Cote
import re
from datetime import datetime
from django.db.models import Max


# Fonctions utilitaires pour extraire des informations spécifiques
def extraire_sport(texte):
    match = re.search(r'-\s*(.*?)\s*\(', texte)
    return match.group(1).strip() if match else ''


def extraire_niveau(texte):
    match = re.search(r'\((.*?)\)', texte)
    return match.group(1).strip() if match else ''


def extraire_poule(texte):
    match = re.search(r'(\w{2})(?= -)', texte)
    return match.group(1).strip() if match else ''


def calculer_cote(match):
    """Calcul de la cote pour un match spécifique."""
    match_id = match.id if match.id else 0
    return round(1 / (1.01 + match_id), 2)


def creer_cotes_pour_match(match):
    """Crée les cotes pour un match spécifique."""
    if match.id is None:
        raise ValueError("Le match doit être sauvegardé avant de créer les cotes.")
    
    cotes = [
        Cote(match=match, type_cote=f"victoire {match.equipe1}", valeur=calculer_cote(match)),
        Cote(match=match, type_cote=f"victoire {match.equipe2}", valeur=1 + calculer_cote(match)),
        Cote(match=match, type_cote="Nul", valeur=2 + calculer_cote(match))
    ]
    # Utilisation de bulk_create pour insérer les cotes en une seule requête
    Cote.objects.bulk_create(cotes)


# Fonction pour télécharger et comparer les fichiers Excel
def export_excel_website(url: str, df_original, name_file: str):
    """
    Télécharge le fichier Excel depuis le site web et compare avec l'ancien fichier.
    """
    try:
        response = requests.post(url)
        if response.status_code == 200:
            with open(name_file, 'wb') as file:
                file.write(response.content)
            print("Fichier téléchargé avec succès !")
            
            # Lecture du fichier Excel
            df_new = pd.read_excel(name_file, engine='openpyxl')
            
            # Supprimer les colonnes dupliquées
            df_new = df_new.loc[:, ~df_new.columns.duplicated()]
            
            if df_original.equals(pd.DataFrame(df_new)):
                print("Les fichiers sont identiques.")
                return df_original, False
            else:
                print("Les fichiers sont différents.")
                return pd.DataFrame(df_new), True
        else:
            print(f"Échec du téléchargement du fichier. Code de statut : {response.status_code}")
            return df_original, False
            
    except Exception as e:
        print(f"Erreur lors de l'export : {str(e)}")
        return df_original, False


# Fonction principale pour importer les matchs
def import_matches_from_url(url, current_df=None):
    if current_df is None:
        current_df = pd.DataFrame()
        
    name_file = 'Export_Resultats.xlsx'
    df, changed = export_excel_website(url, current_df, name_file)
    
    if changed:
        try:
            with transaction.atomic():
                # Générer un ID unique pour chaque match
                max_id = Match.objects.all().aggregate(Max('id'))['id__max'] or 0
                current_id = max_id
                
                for index, row in df.iterrows():
                    date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", 
                                              format='%d/%m/%Y %H:%M')
                    
                    # Vérifier si le match existe déjà
                    existing_match = Match.objects.filter(
                        sport=extraire_sport(row['Poule']),
                        date=date_heure.date(),
                        heure=date_heure.time(),
                        equipe1=row['Équipe 1'].strip(),
                        equipe2=row['Équipe 2'].strip()
                    ).first()
                    
                    if existing_match:
                        # Mettre à jour le match existant
                        existing_match.score1 = int(row['Score 1']) if pd.notna(row['Score 1']) else 0
                        existing_match.score2 = int(row['Score 2']) if pd.notna(row['Score 2']) else 0
                        existing_match.niveau = extraire_niveau(row['Poule'])
                        existing_match.poule = extraire_poule(row['Poule'])
                        existing_match.save()
                        print(f"Match mis à jour: {existing_match}")
                    else:
                        # Créer un nouveau match avec un ID unique
                        current_id += 1
                        match = Match.objects.create(
                            id=current_id,
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
                        print(f"Nouveau match créé: {match}")
                        creer_cotes_pour_match(match)
                        
        except Exception as e:
            print(f"Erreur lors de l'import: {str(e)}")
            return current_df
            
        return df
    return current_df

# Commande Django pour exécuter le script
class Command(BaseCommand):
    help = 'Met à jour les matchs depuis le site FFSU'

    def handle(self, *args, **kwargs):
        self.stdout.write('Début de la mise à jour des matchs...')
        
        url = 'https://sportco.abyss-clients.com/rencontres/resultats/export'
        current_df = pd.DataFrame()
        
        try:
            current_df = import_matches_from_url(url, current_df)
            self.stdout.write(self.style.SUCCESS('Mise à jour terminée avec succès !'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la mise à jour : {str(e)}'))
