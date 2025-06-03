#update_matches.py
#Pour appeler la fonction il faut mettre 'python manage.py update_matches'

from django.core.management.base import BaseCommand
import pandas as pd
import requests
from django.db import transaction
from listings.models import Match, Cote
import re
from datetime import datetime
from django.db.models import Max
import os

# Dictionnaire des académies et leurs GrpId
ACADEMIES_GRPID = {
    'Lyon': 1,
    'Clermont': 3,
    'Grenoble': 4,
    'Saint Etienne': 5,
    'Aix/Marseille': 6,
    'Montpellier': 8,
    'Toulouse': 9,
    'Angers': 11,
    'La Roche-sur-Yon': 12,
    'Bordeaux': 13,
    'Hauts-de-France': 14,
    'Reims': 15,
    'Ile-de-France': 17,
    'Strasbourg': 20,
}

EXCEL_DIR = 'Excels'

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
    match_id = match.id if match.id else 0
    return round(1 / (1.01 + match_id), 2)

def creer_cotes_pour_match(match):
    if match.id is None:
        raise ValueError("Le match doit être sauvegardé avant de créer les cotes.")
    
    cote = Cote(
        match=match,
        coteN=2 + calculer_cote(match),
        cote1=calculer_cote(match),
        cote2=1 + calculer_cote(match)
    )
    cote.save()

def export_excel_website(url: str, df_original, name_file: str, academie: str):
    try:
        response = requests.post(url)
        if response.status_code == 200:
            file_name = f"{academie}_{name_file}"
            file_path = os.path.join(EXCEL_DIR, file_name)
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Fichier {file_name} téléchargé avec succès !")
            
            df_new = pd.read_excel(
                file_path, 
                engine='openpyxl',
                dtype={
                    'Équipe 1': str,
                    'Équipe 2': str,
                    'Poule': str,
                    'Lieu': str,
                    'Score 1': float,
                    'Score 2': float
                }
            )
            
            df_new = df_new.fillna({
                'Équipe 1': '',
                'Équipe 2': '',
                'Poule': '',
                'Lieu': '',
                'Score 1': 0,
                'Score 2': 0
            })
            
            df_new = df_new.loc[:, ~df_new.columns.duplicated()]
            
            if df_original.equals(pd.DataFrame(df_new)):
                print(f"Les fichiers sont identiques pour {academie}.")
                return df_original, False
            else:
                print(f"Les fichiers sont différents pour {academie}.")
                return pd.DataFrame(df_new), True
        else:
            print(f"Échec du téléchargement du fichier pour {academie}. Code de statut : {response.status_code}")
            return df_original, False
            
    except Exception as e:
        print(f"Erreur lors de l'export pour {academie} : {str(e)}")
        return df_original, False

def fusionner_donnees_match(df_planning, df_resultats):
    def create_match_key(row):
        return f"{row['Poule']}_{row['Date']}_{row['Heure']}_{row['Équipe 1']}_{row['Équipe 2']}"
    
    df_planning['match_key'] = df_planning.apply(create_match_key, axis=1)
    df_resultats['match_key'] = df_resultats.apply(create_match_key, axis=1)
    
    df_complet = pd.merge(
        df_planning,
        df_resultats.drop(['Poule', 'Date', 'Heure', 'Équipe 1', 'Équipe 2'], axis=1),
        on='match_key',
        how='outer'
    )
    
    df_complet = df_complet.drop('match_key', axis=1)
    
    return df_complet

def import_matches_from_urls(url_resultats, url_planning, academie, current_df_resultats=None, current_df_planning=None):
    if current_df_resultats is None:
        current_df_resultats = pd.DataFrame()
    if current_df_planning is None:
        current_df_planning = pd.DataFrame()
    
    df_resultats, changed_resultats = export_excel_website(url_resultats, current_df_resultats, 'Export_Resultats.xlsx', academie)
    df_planning, changed_planning = export_excel_website(url_planning, current_df_planning, 'Export_Planning.xlsx', academie)
    
    if not (changed_resultats or changed_planning):
        return current_df_resultats, current_df_planning
        
    df_complet = fusionner_donnees_match(df_planning, df_resultats)
    
    matches_to_create = []
    seen_matches = set()
    max_id = Match.objects.aggregate(Max('id'))['id__max'] or 0
    current_id = max_id + 1
    
    try:
        df_complet['Date'] = df_complet['Date'].astype(str)
        df_complet['Heure'] = df_complet['Heure'].astype(str)
        
        bool_columns = ['M. Joué', 'Forf. 1', 'Forf. 2', 'F. 1 n.d.', 'F. 2 n.d.']
        for col in bool_columns:
            if col in df_complet.columns:
                df_complet[col] = df_complet[col].fillna("").apply(lambda x: True if x == 'X' else False)
        
        for index, row in df_complet.iterrows():
            try:
                if pd.notna(row['Date']) and pd.notna(row['Heure']):
                    date_heure = pd.to_datetime(f"{row['Date']} {row['Heure']}", format='%d/%m/%Y %H:%M', errors='coerce')
                else:
                    date_heure = None
                
                equipe1 = str(row['Équipe 1']).strip() if pd.notna(row['Équipe 1']) else ''
                equipe2 = str(row['Équipe 2']).strip() if pd.notna(row['Équipe 2']) else ''
                
                if pd.isna(date_heure):
                    print(f"Date invalide ligne {index} pour {academie}")
                    continue

                match_key = (
                    extraire_sport(row['Poule']),
                    date_heure.date(),
                    date_heure.time(),
                    equipe1,
                    equipe2
                )
                
                lieu = row.get('Lieu', '').strip()
                
                match_existant = Match.objects.filter(
                    sport=match_key[0],
                    date=match_key[1],
                    heure=match_key[2],
                    equipe1=match_key[3],
                    equipe2=match_key[4],
                    academie=academie
                ).exclude(equipe1__startswith='TEST_').first()

                if match_existant:
                    match_existant.lieu = lieu
                    match_existant.arbitre = row.get('Arbitre(s)', '')
                    match_existant.commentaires = row.get('Commentaires', '')
                    match_existant.academie = academie
                    match_existant.save()
                    continue
                    
                if match_key in seen_matches:
                    continue
                    
                seen_matches.add(match_key)
                match = Match(
                    id=current_id,
                    sport=match_key[0],
                    date=match_key[1],
                    heure=match_key[2],
                    equipe1=equipe1,
                    equipe2=equipe2,
                    score1=int(row['Score 1']) if pd.notna(row.get('Score 1')) else 0,
                    score2=int(row['Score 2']) if pd.notna(row.get('Score 2')) else 0,
                    niveau=extraire_niveau(row['Poule']),
                    poule=extraire_poule(row['Poule']),
                    match_joue=row.get('M. Joué', False),
                    forfait_1=row.get('Forf. 1', False),
                    forfait_2=row.get('Forf. 2', False),
                    lieu=lieu,
                    academie=academie
                )
                matches_to_create.append(match)
                current_id += 1
                
            except Exception as e:
                print(f"Erreur ligne {index} pour {academie}: {str(e)}")
                continue

        if matches_to_create:
            with transaction.atomic():
                Match.objects.bulk_create(matches_to_create)
                for match in matches_to_create:
                    creer_cotes_pour_match(match)
            print(f"{len(matches_to_create)} nouveaux matchs créés pour {academie}")
        else:
            print(f"Aucun nouveau match à créer pour {academie}")
                
    except Exception as e:
        print(f"Erreur import pour {academie}: {str(e)}")
        return current_df_resultats, current_df_planning
        
    return df_resultats, df_planning

class Command(BaseCommand):
    help = 'Met à jour les matchs depuis le site FFSU avec données de planning et résultats pour toutes les académies'

    def handle(self, *args, **kwargs):
        self.stdout.write('Début de la mise à jour des matchs pour toutes les académies...')
        
        base_url_resultats = 'https://sportco.abyss-clients.com/rencontres/resultats/export?id=1&GrpId='
        base_url_planning = 'https://sportco.abyss-clients.com/rencontres/planning/export?id=1&GrpId='
        
        for academie, grp_id in ACADEMIES_GRPID.items():
            self.stdout.write(f'\nTraitement de l\'académie {academie}...')
            
            # AJOUTE CETTE LIGNE - Suppression des anciens matchs MAIS PAS les matchs de test
            Match.objects.filter(academie=academie).exclude(equipe1__startswith='TEST_').delete()
            self.stdout.write(f'Anciens matchs supprimés pour {academie} (matchs de test préservés)')

            url_resultats = f"{base_url_resultats}{grp_id}"
            url_planning = f"{base_url_planning}{grp_id}"
            
            current_df_resultats = pd.DataFrame()
            current_df_planning = pd.DataFrame()
            
            try:
                current_df_resultats, current_df_planning = import_matches_from_urls(
                    url_resultats, 
                    url_planning, 
                    academie,
                    current_df_resultats, 
                    current_df_planning
                )
                self.stdout.write(self.style.SUCCESS(f'Mise à jour terminée avec succès pour {academie} !'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de la mise à jour pour {academie} : {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS('\nMise à jour terminée pour toutes les académies !'))