from django.contrib import admin

from background.actualisation_bdd import Match
from django.contrib.auth.models import User
from listings.models import UserPoints
from listings.models import Cote, Pari, photo_profil

admin.site.register(Match)
admin.site.register(UserPoints)
admin.site.register(Cote)
admin.site.register(Pari)
admin.site.register(photo_profil)
# Register your models here.

