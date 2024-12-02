import export_excel
import pandas as pd
from django.db import models, transaction
import time
from background.creation_bdd import match  # Remplacez par votre modèle
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database(df_diff):
    """
    Met à jour la base de données avec les différences trouvées
    """
    created_count = 0
    updated_count = 0
    
    try:
        with transaction.atomic():
            for _, row in df_diff.iterrows():
                # Convertir la ligne en dictionnaire et supprimer la colonne 'source'
                data = row.drop('source').to_dict()
                
                # Utilisez les champs qui identifient de manière unique votre entrée
                # Par exemple, si vous avez un champ 'id' ou 'reference'
                unique_fields = {
                    'field1': data['field1'],  # Remplacez par vos champs uniques
                    'field2': data['field2']   # Remplacez par vos champs uniques
                }
                
                try:
                    if row['source'] == 'df_new':
                        # La ligne est nouvelle ou modifiée dans excel
                        obj, created = match.objects.update_or_create(
                            defaults=data,
                            **unique_fields
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                    elif row['source'] == 'df_original':
                        # La ligne existe dans la base mais pas dans excel
                        # Vous pouvez choisir de la supprimer ou la marquer comme inactive
                        match.objects.filter(**unique_fields).delete()
                        # Ou pour marquer comme inactif si vous avez un champ 'active':
                        # match.objects.filter(**unique_fields).update(active=False)
                
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la ligne {data}: {str(e)}")
                    continue
                    
        logger.info(f"Mise à jour terminée: {created_count} créés, {updated_count} mis à jour")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la transaction: {str(e)}")
        return False

# Votre boucle principale
url = '"oirshgfoifshogdihfoghfoighdfgfd.fr' #URL à modifier selon ce qu'on souhaite
name_file = 'lroghdsogihdfoixwhgbdoifxhdgovdhfxgcoifdh.xls' #Name_file à modifier selon ce qu'on souhaite extraire
while True:
    try:
        [excel, change] = export_excel.export_excel_website(url, df_original, name_file)
        
        if change:
            logger.info("Changements détectés, mise à jour de la base de données...")
            
            # Préparation des DataFrames pour la comparaison
            df_original['source'] = 'df_original'
            excel['source'] = 'df_new'
            
            # Identification des différences
            df_diff = pd.concat([df_original, excel])
            df_diff = df_diff[df_diff.duplicated(subset=df_diff.columns[:-1], keep=False) == False]
            
            # Mise à jour de la base de données
            if not df_diff.empty:
                success = update_database(df_diff)
                if success:
                    # Mise à jour de df_original pour le prochain cycle
                    df_original = excel.copy()
                    logger.info("Base de données mise à jour avec succès")
                else:
                    logger.error("Échec de la mise à jour de la base de données")
            else:
                logger.info("Aucune différence à mettre à jour")
                
    except Exception as e:
        logger.error(f"Erreur dans la boucle principale: {str(e)}")
        
    # Attente avant la prochaine vérification
    time.sleep(3600)  # Attente d'une heure
