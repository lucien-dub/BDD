from background.export_excel import export_excel_website
from django.db import models

while True:
    [data,change]export_excel_website()
    if change == True:
        """effectue les changements dans la base de donnée"""
    time.sleep(3600)

