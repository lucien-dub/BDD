from action.export_planning_FFSU import *
from django.db import models

while True:
    [data,change]export_planning()
    if change == True:
        """effectue les changements dans la base de donnée"""
    time.sleep(3600)


