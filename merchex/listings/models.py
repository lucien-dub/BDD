# listings/models.py

from django.db import models


class Equipes(models.Model):

    class Sport(models.TextChoices):
        Rugby = 'Rugby'
        Football = 'Football'
        Volleyball = 'Volleyball'
        Handball = 'Handball'
        Basketball = 'Basketball'
        Tennis = 'Tennis'


    id = models.AutoField(primary_key=True)
    sport = models.fields.CharField(choices = Sport.choices, max_length = 100)
    name = models.fields.CharField(max_length=100)
    lieu = models.fields.CharField(max_length=100)
    niveau = models.fields.IntegerField()


class Matchs(models.Model):
    date = models.fields.DateField()
    equipe1 = models.ForeignKey(Equipes,related_name='equipe1', on_delete = models.PROTECT)
    equipe2 = models.ForeignKey(Equipes, related_name='equipe2', on_delete = models.PROTECT)
    sport = {"Rugby","Tennis","Football","Basketball","Handball","Volleyball"}
    passe = models.BooleanField()


class MyManager(models.Manager):
    use_in_migrations = True

class MyModel(models.Model):
    objects = MyManager()

