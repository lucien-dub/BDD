# listings/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime
from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal

class MyManager(models.Manager):
    def custom_method(self):
        return self.filter(is_active=True)


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

    @property
    def est_termine(self):
        now = timezone.now()
        match_datetime = datetime.combine(self.date, self.heure)
        return match_datetime.timestamp() <= now.timestamp() or (self.score1 != 0 or self.score2 != 0)

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

class Bet(models.Model):
    id = models.BigAutoField(primary_key=True)
    mise = models.FloatField(max_length=6, default=0)
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    cote_totale = models.FloatField(max_length=5, default=1)

    # Ajout d'une relation avec l'utilisateur
    user = models.ForeignKey(
        User,  # Clé étrangère vers l’utilisateur
        on_delete=models.CASCADE,  # Supprime le pari si l'utilisateur est supprimé
        related_name="bets",  # Permet d’accéder aux paris d'un utilisateur via user.bets.all()
        verbose_name="Utilisateur",
        null = True,
        blank=True
    )

    paris_id = models.JSONField(default=list, verbose_name="IDs des paris")  # Nouveau champ
    paris_cotes = models.JSONField(default=dict, verbose_name="Cotes des paris")

    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bets"
        verbose_name_plural = "Bets"
        ordering = ['-date_creation']


class Pari(models.Model):
    """Modèle pour les paris individuels"""
    id = models.BigAutoField(primary_key=True)

    bet = models.ForeignKey(
        Bet,
        on_delete=models.CASCADE,
        related_name="paris",
        verbose_name="Bet",
        null=True,
        blank=True
    )

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="paris",
        verbose_name="Match"
    )

    CHOIX_RESULTAT = [
        ('1', 'Victoire Équipe 1'),
        ('N', 'Match Nul'),
        ('2', 'Victoire Équipe 2')
    ]

    CHOIX_STATUT = [
        ('NaN', 'En attente'),
        ('1', 'Victoire Équipe 1'),
        ('N', 'Match Nul'),
        ('2', 'Victoire Équipe 2')
    ]

    selection = models.CharField(
        max_length=1,
        choices=CHOIX_RESULTAT,
        verbose_name="Pronostic"
    )

    cote = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name="Cote"
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Pari actif"
    )

    resultat = models.CharField(
        max_length=3,
        choices=CHOIX_STATUT,
        default='NaN',
        verbose_name="Résultat du pari"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    def clean(self):
        if self.match and self.match.est_termine and self.actif:
            raise ValidationError("Impossible de placer un pari sur un match terminé")

    class Meta:
        verbose_name = "Pari"
        verbose_name_plural = "Paris"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Pari {self.get_selection_display()} sur {self.match}"


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