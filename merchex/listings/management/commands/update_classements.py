# update_classements.py
import os
import re
import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from django.core.management import call_command
from listings.models import Classement

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
    match = re.search(r'-\s*([^(]+?)\s*\(', texte)
    return match.group(1).strip() if match else ''

def extraire_niveau(texte):
    match = re.search(r'\(([^-]+?)\s*-', texte)
    return match.group(1).strip() if match else ''


def extraire_poule(texte):
    """
    Extrait les informations de la poule à partir du texte.
    Retourne un dictionnaire avec les clés: 'sport_code', 'periode', 'niveau', 'poule'
    
    Formats supportés:
    - BAD_BRASS_N1P1 - Badminton par équipes (Niveau 1 - MIXTE)
    - BADMINTON_N1P1 - Badminton par équipes (Niveau 1 - MIXTE)
    - RUG M BRAS N1 P1 - Rugby (Niveau 1 - M)
    """
    
    # Pattern pour format avec underscores (BAD_BRASS_N1P1 ou BADMINTON_N1P1)
    pattern_underscore = r'^([A-Z]+)(?:_BRASS|_BRASSAGE)?_N(\d+)P(\d+)'
    match_underscore = re.search(pattern_underscore, texte)
    
    if match_underscore:
        sport_code = match_underscore.group(1)
        niveau = match_underscore.group(2)
        poule = match_underscore.group(3)
        
        # Détermine la période
        if '_BRASS' in texte or '_BRASSAGE' in texte:
            periode = 'brassage'
        else:
            periode = 'reguliere'
        
        return {
            'sport_code': sport_code,
            'niveau': niveau,
            'poule': f"{periode}_P{poule}"
        }
    
    # Pattern pour format avec espaces (RUG M BRAS N1 P1)
    pattern_espace = r'^([A-Z]+)\s+([MF])?\s*(BRAS|BRASSAGE)?\s*N(\d+)\s+P(\d+)'
    match_espace = re.search(pattern_espace, texte)
    
    if match_espace:
        sport_code = match_espace.group(1)
        genre = match_espace.group(2) if match_espace.group(2) else ''
        periode_match = match_espace.group(3)
        niveau = match_espace.group(4)
        poule = match_espace.group(5)
        
        # Détermine la période
        if periode_match and ('BRAS' in periode_match or 'BRASSAGE' in periode_match):
            periode = 'brassage'
        else:
            periode = 'reguliere'
        
        # Construction du code sport complet avec genre si présent
        sport_code_complet = f"{sport_code}_{genre}" if genre else sport_code
        
        return {
            'sport_code': sport_code_complet,
            'niveau': niveau,
            'poule': f"{periode}_P{poule}"
        }
    
    # Pattern de fallback pour extraire au moins la poule si les autres échouent
    fallback_pattern = r'P(\d+)'
    fallback_match = re.search(fallback_pattern, texte)
    
    if fallback_match:
        return {
            'sport_code': 'INCONNU',
            'niveau': '1',
            'poule': fallback_match.group(1),
        }
    
    # Si aucun pattern ne correspond
    return {
        'sport_code': 'INCONNU',
        'niveau': '1',
        'poule': '1',
    }

def export_excel_classements_website(url: str, df_original, name_file: str, academie: str):
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
                    'Poule': str,
                    'Place': float,
                    'Équipe': str,
                    'Pts': float,
                    'J': float,
                    'Pen': float,
                    'G': float,
                    'N': float,
                    'P': float,
                    'GF': float,
                    'PF': float,
                    'G TV': float,
                    'P TV': float,
                    'Ba': float,
                    'Bd': float,
                    'Pour': float,
                    'Contre': float,
                    'Diff.': float
                }
            )
            
            # Remplacer les valeurs NaN par des valeurs par défaut appropriées
            df_new = df_new.fillna({
                'Poule': '',
                'Place': 0,
                'Équipe': '',
                'Pts': 0,
                'J': 0,
                'Pen': 0,
                'G': 0,
                'N': 0,
                'P': 0,
                'GF': 0,
                'PF': 0,
                'G TV': 0,
                'P TV': 0,
                'Ba': 0,
                'Bd': 0,
                'Pour': 0,
                'Contre': 0,
                'Diff.': 0
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

def import_classements_from_url(url_classements, academie, current_df_classements=None):
    if current_df_classements is None:
        current_df_classements = pd.DataFrame()
    
    df_classements, changed = export_excel_classements_website(
        url_classements, 
        current_df_classements, 
        'Export_Classements.xlsx', 
        academie
    )
    
    if not changed:
        return current_df_classements
        
    classements_to_create = []
    classements_to_update = []
    seen_classements = set()
    max_id = Classement.objects.aggregate(Max('id'))['id__max'] or 0
    current_id = max_id + 1
    
    try:
        # Conversion des colonnes numériques
        numeric_columns = ['Place', 'Pts', 'J', 'Pen', 'G', 'N', 'P', 'GF', 'PF', 
                          'G TV', 'P TV', 'Ba', 'Bd', 'Pour', 'Contre', 'Diff.']
        
        for col in numeric_columns:
            if col in df_classements.columns:
                df_classements[col] = pd.to_numeric(df_classements[col], errors='coerce').fillna(0)
        
        for index, row in df_classements.iterrows():
            try:
                poule_complete = str(row['Poule']).strip()
                equipe = str(row['Équipe']).strip() if pd.notna(row['Équipe']) else ''
                print(f'La chaine de la poule est : {poule_complete}')

                if not poule_complete or not equipe:
                    print(f"Données manquantes ligne {index} pour {academie}")
                    continue

                # Créer une clé unique pour éviter les doublons
                classement_key = (
                    extraire_sport(str(row['Poule'])),
                    extraire_niveau(str(row['Poule'])),
                    extraire_poule(str(row['Poule'])),
                    equipe,
                    academie
                )
                
                if classement_key in seen_classements:
                    continue
                    
                seen_classements.add(classement_key)

                # Vérifier si le classement existe déjà
                classement_existant = Classement.objects.filter(
                    sport=classement_key[0],
                    niveau=classement_key[1],
                    poule=classement_key[2],
                    equipe=classement_key[3],
                    academie=academie
                ).first()
                
                
                print(f'Sport trouvé : {classement_key[0]}, Niveau trouvé {classement_key[1]}, Poule trouvée : {classement_key[2]}')

                classement_data = {
                    'sport': classement_key[0],
                    'niveau': classement_key[1],
                    'poule': classement_key[2],
                    'equipe': equipe,
                    'place': int(row.get('Place', 0)),
                    'points': int(row.get('Pts', 0)),
                    'joues': int(row.get('J', 0)),
                    'penalites': int(row.get('Pen', 0)),
                    'gagnes': int(row.get('G', 0)),
                    'nuls': int(row.get('N', 0)),
                    'perdus': int(row.get('P', 0)),
                    'gagnes_forfait': int(row.get('GF', 0)),
                    'perdus_forfait': int(row.get('PF', 0)),
                    'gagnes_tv': int(row.get('G TV', 0)),
                    'perdus_tv': int(row.get('P TV', 0)),
                    'buts_avantage': int(row.get('Ba', 0)),
                    'buts_desavantage': int(row.get('Bd', 0)),
                    'pour': int(row.get('Pour', 0)),
                    'contre': int(row.get('Contre', 0)),
                    'difference': int(row.get('Diff.', 0)),
                    'academie': academie
                }

                if classement_existant:
                    # Mettre à jour le classement existant
                    for key, value in classement_data.items():
                        if key != 'id':
                            setattr(classement_existant, key, value)
                    classements_to_update.append(classement_existant)
                else:
                    # Créer un nouveau classement
                    classement = Classement(
                        id=current_id,
                        **classement_data
                    )
                    classements_to_create.append(classement)
                    current_id += 1
                
            except Exception as e:
                print(f"Erreur ligne {index} pour {academie}: {str(e)}")
                continue

        # Sauvegarder les modifications
        with transaction.atomic():
            if classements_to_create:
                Classement.objects.bulk_create(classements_to_create)
                print(f"{len(classements_to_create)} nouveaux classements créés pour {academie}")
                
            if classements_to_update:
                # Mise à jour par lot
                for classement in classements_to_update:
                    classement.save()
                print(f"{len(classements_to_update)} classements mis à jour pour {academie}")
                
            if not classements_to_create and not classements_to_update:
                print(f"Aucun classement à créer ou mettre à jour pour {academie}")
                
    except Exception as e:
        print(f"Erreur import classements pour {academie}: {str(e)}")
        return current_df_classements
        
    return df_classements

class Command(BaseCommand):
    help = 'Met à jour les classements depuis le site FFSU pour toutes les académies'

    def handle(self, *args, **kwargs):
        self.stdout.write('Début de la mise à jour des classements pour toutes les académies...')
        
        base_url_classements = 'https://sportco.abyss-clients.com/rencontres/classements/export?id=1&GrpId='
        
        for academie, grp_id in ACADEMIES_GRPID.items():
            self.stdout.write(f'\nTraitement de l\'académie {academie}...')

            url_classements = f"{base_url_classements}{grp_id}"
            
            current_df_classements = pd.DataFrame()
            
            try:
                current_df_classements = import_classements_from_url(
                    url_classements, 
                    academie,
                    current_df_classements
                )
                self.stdout.write(self.style.SUCCESS(f'Mise à jour terminée avec succès pour {academie} !'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de la mise à jour pour {academie} : {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS('\nMise à jour terminée pour toutes les académies !'))