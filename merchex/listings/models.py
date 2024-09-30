# listings/models.py

from django.db import models

class Band(models.Model):
    name = models.fields.CharField(max_length=100)

class MyManager(models.Manager):
    use_in_migrations = True

class MyModel(models.Model):
    objects = MyManager()

