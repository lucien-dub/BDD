from django.contrib import admin

from background.actualisation_bdd import Match
from django.contrib.auth.models import User
from listings.models import UserPoints
from listings.models import Cote

admin.site.register(Match)
admin.site.register(UserPoints)
admin.site.register(Cote)
# Register your models here.

