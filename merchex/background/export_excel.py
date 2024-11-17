#import pandas as pd
# Define the URL and the data you want to send with the POST request
#url = 'https://sportco.abyss-clients.com/rencontres/planning/export'
#df_original = pd.DataFrame([2,4,6])    # mettre un dataframe random pour télécharger le fichier au début

def export_excel_website(url : str,df_original, name_file : str):
    """
    Fonction permettant d'aller faire une requete POST pour exporter le fichier excel planning sur le site de la FFSU 
    """
    import requests
    import pandas as pd 

    response = requests.post(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the content of the response to a file
        with open(name_file, 'wb') as file:
            file.write(response.content)
        print("File downloaded successfully!")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

    # File to check
    df_new = pd.DataFrame(pd.read_excel(name_file))

    # compare les deux dataframes
    if df_original.equals(df_new):
        print("Les fichiers sont identiques.")
        change = False
    else:
        print("Les fichiers sont différents.")
        df_original = df_new
        change = True

    return(df_original, change)
    