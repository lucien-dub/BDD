from background.export_excel import export_excel_website
from django.db import models
import pandas as pd
from django.db import models, transaction
import time
from listings.models import Match
import logging
import listings


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
                        obj, created = listings.objects.update_or_create(
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
                        listings.objects.filter(**unique_fields).delete()
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
url = 'http://sportco.abyss-clients.com/rencontres/resultats/export' #URL à modifier selon ce qu'on souhaite
name_file = 'export_resultat.xlsx' #Name_file à modifier selon ce qu'on souhaite extraire
df_original = pd.DataFrame() #dataframe vide

"""while True:
[data,change] = export_excel_website(url,df_original,name_file)
    if change == True:
        """#effectue les changements dans la base de donnée"""
"""time.sleep(3600)"""