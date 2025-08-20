# listings/management/commands/update_classements.py
import os
import re
import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
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
    match = re.search(r'\((.*?)\)', texte)
    return match.group(1).strip() if match else ''

def extraire_poule(texte):
    match = re.search(r'(\w{2})(?= -)', texte)
    return match.group(1).strip() if match else ''


def export_excel_classements_website(url, df_original, filename, academie):
    try:
        
        response = requests.get(url)
        
        if response.status_code == 200:
            file_path = os.path.join(EXCEL_DIR, filename)
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            
            df_new = pd.read_excel(file_path)
            
            if df_new.empty:
                print(f"Le fichier Excel téléchargé pour {academie} est vide.")
                return df_original, False
            
            # Standardisation des colonnes par défaut si elles n'existent pas
            default_columns = {
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
            }
            
            for col, default_val in default_columns.items():
                if col not in df_new.columns:
                    df_new[col] = default_val
            
            df_new = df_new.loc[:, ~df_new.columns.duplicated()]
            
            if not df_original.empty and df_original.equals(pd.DataFrame(df_new)):
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
    
    try:
        # Obtenir l'ID maximum actuel
        max_id = Classement.objects.aggregate(Max('id'))['id__max'] or 0
        current_id = max_id + 1
        
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

                if not poule_complete or not equipe:
                    print(f"Données manquantes ligne {index} pour {academie}")
                    continue

                # Extraction des informations de poule avec la nouvelle fonction
                poule_info = extraire_poule(poule_complete)
                sport = extraire_sport(poule_complete)
                niveau = extraire_niveau(poule_complete)
                
                # Utilisation des informations extraites
                sport_final = sport if sport else poule_info['sport_code']
                niveau_final = niveau if niveau else f"Niveau {poule_info['niveau']}"
                
                # Création de la clé de classement avec période
                classement_key = (
                    sport_final, 
                    niveau_final, 
                    poule_info['poule_complete'],
                    equipe
                )

                if classement_key in seen_classements:
                    continue
                
                seen_classements.add(classement_key)

                # Vérifier si le classement existe déjà
                classement_existant = Classement.objects.filter(
                    sport=sport_final,
                    niveau=niveau_final,
                    poule=poule_info['poule_complete'],
                    equipe=equipe,
                    academie=academie
                ).first()

                classement_data = {
                    'sport': sport_final,
                    'niveau': niveau_final,
                    'poule': poule_info['poule_complete'],
                    'periode': poule_info['periode'],
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
        
        # Créer le répertoire Excel s'il n'existe pas
        if not os.path.exists(EXCEL_DIR):
            os.makedirs(EXCEL_DIR)
        
        current_df = pd.DataFrame()
        
        for academie, grp_id in ACADEMIES_GRPID.items():
            self.stdout.write(f'\nTraitement de l\'académie {academie}...')
            
            url_classements = f"{base_url_classements}{grp_id}"
            
            try:
                current_df = import_classements_from_url(
                    url_classements, 
                    academie, 
                    current_df
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Académie {academie} traitée avec succès')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour l\'académie {academie}: {str(e)}')
                )
                continue
        
        self.stdout.write(
            self.style.SUCCESS('Mise à jour des classements terminée pour toutes les académies')
        )
