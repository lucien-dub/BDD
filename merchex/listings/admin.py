from django.contrib import admin

from background.actualisation_bdd import Match
from django.contrib.auth.models import User
from listings.models import UserPoints

admin.site.register(Match)
admin.site.register(UserPoints)
# Register your models here.

