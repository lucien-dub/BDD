# update_classements.py
import os
import re
import pandas as pd
import requests

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
            'periode': periode,
            'niveau': niveau,
            'poule': poule,
            'poule_complete': f"{sport_code}_{periode}_N{niveau}P{poule}"
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
            'periode': periode,
            'niveau': niveau,
            'poule': poule,
            'poule_complete': f"{sport_code_complet}_{periode}_N{niveau}P{poule}"
        }
    
    # Pattern de fallback pour extraire au moins la poule si les autres échouent
    fallback_pattern = r'P(\d+)'
    fallback_match = re.search(fallback_pattern, texte)
    
    if fallback_match:
        return {
            'sport_code': 'INCONNU',
            'periode': 'reguliere',
            'niveau': '1',
            'poule': fallback_match.group(1),
            'poule_complete': f"INCONNU_reguliere_N1P{fallback_match.group(1)}"
        }
    
    # Si aucun pattern ne correspond
    return {
        'sport_code': 'INCONNU',
        'periode': 'reguliere',
        'niveau': '1',
        'poule': '1',
        'poule_complete': 'INCONNU_reguliere_N1P1'
    }

def export_excel_classements_website(url, df_original, filename, academie):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        
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
    max_id = 0  # Vous devrez gérer l'ID différemment sans Django ORM
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
                    poule_info['poule_complete'],  # Utilisation de la poule complète avec période
                    equipe
                )
                
                print(f"Sport: {sport_final}, Niveau: {niveau_final}, Poule: {poule_info['poule_complete']}, Période: {poule_info['periode']}")

                if classement_key in seen_classements:
                    print(f"Classement dupliqué ignoré: {classement_key}")
                    continue
                
                seen_classements.add(classement_key)

                classement_data = {
                    'sport': sport_final,
                    'niveau': niveau_final,
                    'poule': poule_info['poule_complete'],
                    'periode': poule_info['periode'],  # Ajout du champ période
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

                # Ici vous devrez adapter selon votre méthode de stockage
                # (base de données, fichier, etc.)
                classements_to_create.append(classement_data)
                current_id += 1
                
            except Exception as e:
                print(f"Erreur ligne {index} pour {academie}: {str(e)}")
                continue

        print(f"Traités {len(classements_to_create)} classements pour {academie}")
        return df_classements
        
    except Exception as e:
        print(f"Erreur lors de l'import des classements pour {academie}: {str(e)}")
        return current_df_classements
