from django.contrib import admin

from django.contrib.auth.models import User
from listings.models import Match, UserPoints, Cote, Pari, photo_profil
from listings.models import Verification, EmailVerificationToken, UserLoginTracker, Classement

admin.site.register(Match)
admin.site.register(UserPoints)
admin.site.register(Cote)
admin.site.register(Pari)
admin.site.register(photo_profil)
admin.site.register(Verification)
admin.site.register(EmailVerificationToken)
admin.site.register(UserLoginTracker)
admin.site.register(Classement)


