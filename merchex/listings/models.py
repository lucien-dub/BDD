# listings/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class MyManager(models.Manager):
    def custom_method(self):
        return self.filter(is_active=True)

class Listing(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # Attacher le gestionnaire personnalisé
    objects = MyManager()

    def __str__(self):
        return self.name

class Match(models.Model):
    id = models.IntegerField(primary_key=True)
    sport = models.CharField(max_length=50)
    date = models.DateField()
    heure = models.TimeField()
    equipe1 = models.CharField(max_length=200)
    equipe2 = models.CharField(max_length=200)
    score1 = models.IntegerField()  
    score2 = models.IntegerField()
    niveau = models.CharField(max_length=50)
    poule = models.CharField(max_length=50)

    class Meta:
        db_table = 'creation_bdd_match'
        unique_together = ('sport', 'date', 'heure', 'equipe1', 'equipe2')
    
    def __str__(self):
        return f"{self.equipe1} vs {self.equipe2} - {self.date}"
    
class Cote(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="cotes")
    coteN = models.FloatField(max_length=5, default = 1.1)
    cote1 = models.FloatField(max_length=5, default = 1.1)
    cote2 = models.FloatField(max_length=5, default = 1.1)

    def __str__(self):
        return f"Cote pour {self.match},équipe1: {self.cote1}, équipe2: {self.cote2}, match nul :{self.coteN}"



class UserPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_points')
    total_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)


    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"

    @classmethod
    def get_or_create_points(cls, user):
        user_points, created = cls.objects.get_or_create(
            user=user,
            defaults={'total_points': 0}
        )
        return user_points
    
class PointTransaction(models.Model):
    EARN = 'EARN'
    SPEND = 'SPEND'
    
    TRANSACTION_TYPES = [
        (EARN, 'Points gagnés'),
        (SPEND, 'Points dépensés'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.points} points"    