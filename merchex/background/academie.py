import pandas as pd
import requests
import json
from pathlib import Path
import time
import re

def charger_cache():
    """Charge le cache existant ou crée un nouveau."""
    cache_file = Path("cache_villes.json")
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def sauvegarder_cache(cache):
    """Sauvegarde le cache dans un fichier."""
    with open("cache_villes.json", "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_departement_from_api(ville):
    """
    Récupère le département d'une ville via l'API Adresse.
    Retourne (département, score) ou (None, 0) si non trouvé
    """
    base_url = "https://api-adresse.data.gouv.fr/search/"
    params = {
        "q": ville,
        "limit": 1,
        }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if data["features"]:
            properties = data["features"][0]["properties"]
            score = properties.get("score", 0)
            dept = properties.get("context", "").split(",")[0].strip()
            return dept, score
    except Exception as e:
        print(f"Erreur pour la ville {ville}: {str(e)}")

    return None, 0

def get_academie_from_dept(dept):
    """Renvoie l'académie correspondant au département."""
    dept_academies = {
        # Île-de-France
        "75": "Paris", "77": "Créteil", "78": "Versailles",
        "91": "Versailles", "92": "Versailles", "93": "Créteil",
        "94": "Créteil", "95": "Versailles",

        # Auvergne-Rhône-Alpes
        "01": "Lyon", "03": "Clermont-Ferrand", "07": "Grenoble",
        "15": "Clermont-Ferrand", "26": "Grenoble", "38": "Grenoble",
        "42": "Lyon", "43": "Clermont-Ferrand", "63": "Clermont-Ferrand",
        "69": "Lyon", "73": "Grenoble", "74": "Grenoble",

        # Bourgogne-Franche-Comté
        "21": "Dijon", "25": "Besançon", "39": "Besançon",
        "58": "Dijon", "70": "Besançon", "71": "Dijon",
        "89": "Dijon", "90": "Besançon",

        # Bretagne
        "22": "Rennes", "29": "Rennes", "35": "Rennes", "56": "Rennes",

        # Centre-Val de Loire
        "18": "Orléans-Tours", "28": "Orléans-Tours", "36": "Orléans-Tours",
        "37": "Orléans-Tours", "41": "Orléans-Tours", "45": "Orléans-Tours",

        # Grand Est
        "08": "Reims", "10": "Reims", "51": "Reims",
        "52": "Reims", "54": "Nancy-Metz", "55": "Nancy-Metz",
        "57": "Nancy-Metz", "67": "Strasbourg", "68": "Strasbourg",
        "88": "Nancy-Metz",

        # Hauts-de-France
        "02": "Amiens", "59": "Lille", "60": "Amiens",
        "62": "Lille", "80": "Amiens",

        # Normandie
        "14": "Caen", "27": "Rouen", "50": "Caen",
        "61": "Caen", "76": "Rouen",

        # Nouvelle-Aquitaine
        "16": "Poitiers", "17": "Poitiers", "19": "Limoges",
        "23": "Limoges", "24": "Bordeaux", "33": "Bordeaux",
        "40": "Bordeaux", "47": "Bordeaux", "64": "Bordeaux",
        "79": "Poitiers", "86": "Poitiers", "87": "Limoges",

        # Occitanie
        "09": "Toulouse", "11": "Montpellier", "12": "Toulouse",
        "30": "Montpellier", "31": "Toulouse", "32": "Toulouse",
        "34": "Montpellier", "46": "Toulouse", "48": "Montpellier",
        "65": "Toulouse", "66": "Montpellier", "81": "Toulouse",
        "82": "Toulouse",

        # Pays de la Loire
        "44": "Nantes", "49": "Nantes", "53": "Nantes",
        "72": "Nantes", "85": "Nantes",

        # Provence-Alpes-Côte d'Azur
        "04": "Aix-Marseille", "05": "Aix-Marseille", "06": "Nice",
        "13": "Aix-Marseille", "83": "Nice", "84": "Aix-Marseille",

        # Corse
        "2A": "Corse", "2B": "Corse",

        # Outre-mer
        "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
        "974": "La Réunion", "976": "Mayotte",

        # Collectivités d'outre-mer
        "975": "Saint-Pierre-et-Miquelon", "977": "Saint-Barthélemy",
        "978": "Saint-Martin", "986": "Wallis-et-Futuna",
        "987": "Polynésie française", "988": "Nouvelle-Calédonie"
 }

    if dept and (dept.isdigit() or dept in ["2A", "2B"]):
        return dept_academies.get(dept, f"Académie du département {dept}")
    return None

def identifier_ville(lieu):
    """
    Tente d'identifier une ville dans une chaîne de caractères de manière plus précise.
    Retourne (ville, score) ou (None, 0) si aucune ville n'est identifiée.
    """
    # Liste de mots à exclure (à compléter selon vos besoins)
    mots_exclus = {'gymnase', 'stade', 'salle', 'complexe', 'sportif', 'centre', 
                   'isae', 'supaero', 'université', 'campus', 'école', 'college', 
                   'lycée', 'institut', 'parking', 'terrain'}
    
    # Nettoyer la chaîne
    lieu = lieu.lower().strip()
    
    # Première tentative : chercher la ville entière
    dept, score = get_departement_from_api(lieu)
    if dept and score > 0.8:  # Score élevé = correspondance exacte
        return lieu, score

    # Deuxième tentative : découper et tester des combinaisons de mots
    mots = [mot for mot in lieu.split() if mot not in mots_exclus]
    
    meilleure_ville = None
    meilleur_score = 0
    
    # Tester des combinaisons de mots consécutifs
    for i in range(len(mots)):
        for j in range(i + 1, min(i + 4, len(mots) + 1)):  # Test jusqu'à 3 mots consécutifs
            ville_test = " ".join(mots[i:j])
            dept, score = get_departement_from_api(ville_test)
            if dept and score > meilleur_score:
                meilleure_ville = ville_test
                meilleur_score = score

    if meilleur_score > 0.5:  # Seuil de confiance minimum
        return meilleure_ville, meilleur_score
    
    return None, 0

def associer_academies(df, colonne_lieu='Lieu'):
    """
    Associe les académies aux lieux en utilisant un système de cache et une détection plus précise des villes.
    """
    cache = charger_cache()
    nouveaux_resultats = {}

    def get_academie(lieu):
        if lieu in cache:
            return cache[lieu]

        if not isinstance(lieu, str):
            return "Académie non trouvée"

        time.sleep(0.1)  # Respect des limites de l'API

        ville, score = identifier_ville(lieu)
        if ville and score > 0.5:
            dept, _ = get_departement_from_api(ville)
            if dept:
                academie = get_academie_from_dept(dept)
                if academie:
                    nouveaux_resultats[lieu] = academie
                    return academie

        nouveaux_resultats[lieu] = "Académie non trouvée"
        return "Académie non trouvée"

    lieux_uniques = df[colonne_lieu].unique()
    print(f"Traitement de {len(lieux_uniques)} lieux uniques...")

    for lieu in lieux_uniques:
        if lieu not in cache:
            academie = get_academie(lieu)
            print(f"{lieu} -> {academie}")

    cache.update(nouveaux_resultats)
    sauvegarder_cache(cache)

    df['Académie'] = df[colonne_lieu].map(cache)
    return df

if __name__ == "__main__":
    try:
        df = pd.read_excel("Export_Planning.xlsx")
        df = associer_academies(df)
        print("\nCorrespondances trouvées :")
        print(df[['Lieu', 'Académie']].drop_duplicates())
    except Exception as e:
        print(f"Erreur lors du traitement : {str(e)}")