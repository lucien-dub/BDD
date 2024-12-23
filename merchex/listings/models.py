# listings/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser


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
    equipe1 = models.CharField(max_length=100)
    equipe2 = models.CharField(max_length=100)
    score1 = models.IntegerField()  
    score2 = models.IntegerField()
    niveau = models.CharField(max_length=50)
    poule = models.CharField(max_length=50)

    class Meta:
        db_table = 'creation_bdd_match'
    
    def __str__(self):
        return f"{self.equipe1} vs {self.equipe2} - {self.date}"
    
class Cote(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="cotes")
    type_cote = models.CharField(max_length=50)  # Par exemple, "victoire", "nul", etc.
    valeur = models.FloatField(validators=[MinValueValidator(1.01)])

    def __str__(self):
        return f"Cote {self.type_cote} pour {self.match}: {self.valeur}"
    

class CustomUser(AbstractUser):
    points = models.IntegerField(default=0)


