"""
Fonction permettant d'aller faire une requete POST pour exporter le fichier excel planning sur le site de la FFSU 
"""

# URL du fichier à télécharger
import requests
import pandas as pd 
import time
                      
# Define the URL and the data you want to send with the POST request
url = 'https://sportco.abyss-clients.com/rencontres/planning/export'
df_original = pd.DataFrame([2,4,6])    # mettre un dataframe random pour télécharger le fichier au début

while True :
    # Make the POST request
    response = requests.post(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content of the response to a file
        with open('export_planning.xlsx', 'wb') as file:
            file.write(response.content)
        print("File downloaded successfully!")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

    # File to check
    file_name = 'export_planning.xlsx' 
    df_new = pd.DataFrame(pd.read_excel(file_name))

    # compare les deux dataframes
    if df_original.equals(df_new):
        print("Les fichiers sont identiques.")
    else:
        print("Les fichiers sont différents.")
        df_original = df_new

    #stoppe la boucle pendant
    time_to_wait = 86400 #secondes
    time.sleep(time_to_wait)
    

    