# URL du fichier à télécharger
import requests
import pandas as pd 
import hashlib
                      
# Define the URL and the data you want to send with the POST request
url = 'https://sportco.abyss-clients.com/rencontres/planning/export'

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

# Open,close, read file and calculate MD5 on its contents 
with open(file_name, 'rb') as file_to_check:
    # read contents of the file
    data = file_to_check.read()    
    md5_returned = hashlib.md5(data).hexdigest

original_md5 = '6e2a75253d379a3e7583d86c140e9286'    # mettre l'ancien hash du fichier

# Finally compare original MD5 with freshly calculated and convert it to a dataframes
if original_md5 == md5_returned:
    print("MD5 verified.")
else:
    print("MD5 verification failed!.")
    original_md5 = md5_returned
    dfPlanning = pd.DataFrame(pd.read_excel(file_name))
    print(dfPlanning)

    