# URL du fichier à télécharger
import requests
import pandas as pd 

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


# read an excel file and convert into a dataframe object 
df = pd.DataFrame(pd.read_excel("export_planning.xlsx")) 
# show the dataframe 
print(df) 