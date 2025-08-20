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
    """Extrait les informations de sport, niveau et poule depuis le titre."""
    print(f"Analyse de la chaîne : '{texte}'")

    # Supprime les espaces en début et fin
    texte = texte.strip()

    # Pattern principal pour extraire toutes les informations
    pattern_complet = r'^(\d+)\s*-\s*([A-Z\s]+)\s*\((.*?)\s*-\s*([MF]?)\s*\)\s*(?:.*?P(\d+))?'
    match_complet = re.search(pattern_complet, texte, re.IGNORECASE)

    if match_complet:
        sport_code = match_complet.group(1)
        sport_name = match_complet.group(2).strip()
        niveau = match_complet.group(3).strip()
        genre = match_complet.group(4) if match_complet.group(4) else ''
        poule = match_complet.group(5) if match_complet.group(5) else '1'

        # Construction du code sport complet avec genre si présent
        sport_code_complet = f"{sport_code}_{genre}" if genre else sport_code

        print(f"Pattern complet trouvé - Sport: {sport_code_complet}, Niveau: {niveau}, Poule: reguliere_P{poule}")
        return (sport_code_complet, niveau, f"reguliere_P{poule}")

    # Pattern alternatif avec espaces
    pattern_espace = r'^(\d+)\s*-\s*([A-Z\s]+)\s*\(\s*([^)]*?)\s*-\s*([MF]?)\s*\)\s*(?:.*?P(\d+))?'
    match_espace = re.search(pattern_espace, texte, re.IGNORECASE)

    if match_espace:
        sport_code = match_espace.group(1)
        sport_name = match_espace.group(2).strip()
        niveau_et_periode = match_espace.group(3).strip()
        genre = match_espace.group(4) if match_espace.group(4) else ''
        poule = match_espace.group(5) if match_espace.group(5) else '1'

        # Sépare niveau et période si présente
        niveau = niveau_et_periode
        periode = 'reguliere'

        if 'BRAS' in niveau_et_periode.upper():
            periode = 'brassage'
            # Retire BRASSAGE du niveau
            niveau = re.sub(r'\s*BRAS.*', '', niveau_et_periode, flags=re.IGNORECASE).strip()

        # Construction du code sport complet avec genre si présent
        sport_code_complet = f"{sport_code}_{genre}" if genre else sport_code

        print(f"Pattern espace trouvé - Sport: {sport_code_complet}, Niveau: {niveau}, Poule: {periode}_P{poule}")
        return (sport_code_complet, niveau, f"{periode}_P{poule}")

    # Pattern de fallback pour extraire au moins la poule si les autres échouent
    fallback_pattern = r'P(\d+)'
    fallback_match = re.search(fallback_pattern, texte)

    if fallback_match:
        print(f"Pattern fallback trouvé - Poule: P{fallback_match.group(1)}")
        return ('INCONNU', 'INCONNU', f"P{fallback_match.group(1)}")

    # Si aucun pattern ne correspond, essayons de parser manuellement
    # Pour le cas "2000 - RUGBY (Niveau universitaire - M)"
    manual_pattern = r'^(\d+)\s*-\s*([A-Z\s]+)\s*\(\s*([^-]+)\s*-\s*([MF]?)\s*\)$'
    manual_match = re.search(manual_pattern, texte, re.IGNORECASE)
    
    if manual_match:
        sport_code = manual_match.group(1)
        sport_name = manual_match.group(2).strip()
        niveau = manual_match.group(3).strip()
        genre = manual_match.group(4) if manual_match.group(4) else ''
        
        sport_code_complet = f"{sport_code}_{genre}" if genre else sport_code
        
        print(f"Pattern manuel trouvé - Sport: {sport_code_complet}, Niveau: {niveau}, Poule: reguliere_P1")
        return (sport_code_complet, niveau, "reguliere_P1")

    # Si aucun pattern ne correspond
    print(f"Aucun pattern trouvé pour: '{texte}' - Utilisation des valeurs par défaut")
    return ('INCONNU', 'INCONNU', 'reguliere_P1')

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

                # Extraire les informations de la poule
                sport, niveau, poule = extraire_poule(poule_complete)
                
                # Créer une clé unique pour éviter les doublons (maintenant avec 4 éléments)
                classement_key = (sport, niveau, poule, equipe)

                if classement_key in seen_classements:
                    continue

                seen_classements.add(classement_key)

                # Vérifier si le classement existe déjà
                classement_existant = Classement.objects.filter(
                    sport=sport,
                    niveau=niveau,
                    poule=poule,
                    equipe=equipe,
                    academie=academie
                ).first()

                print(f'Sport trouvé : {sport}, Niveau trouvé {niveau}, Poule trouvée : {poule}, Équipe : {equipe}')

                classement_data = {
                    'sport': sport,
                    'niveau': niveau,
                    'poule': poule,
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