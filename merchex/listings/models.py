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


class GroupePari(models.Model):
    """Modèle pour tous les types de paris (simples ou combinés)"""
    id = models.BigAutoField(primary_key=True)
    
    mise = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Mise totale"
    )
    
    cote_totale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name="Cote totale"
    )
    
    gain_potentiel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Gain potentiel"
    )
    
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('GAGNE', 'Gagné'),
        ('PERDU', 'Perdu'),
        ('ANNULE', 'Annulé')
    ]
    
    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='EN_COURS',
        verbose_name="Statut du groupe"
    )
    
    TYPE_CHOICES = [
        ('SIMPLE', 'Pari simple'),
        ('COMBINE', 'Pari combiné')
    ]
    
    type_pari = models.CharField(
        max_length=7,
        choices=TYPE_CHOICES,
        default='SIMPLE',
        verbose_name="Type de pari"
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    def calculer_cote_totale(self):
        cote_totale = Decimal('1.0')
        for pari in self.paris.filter(actif=True):
            cote_totale *= pari.cote
        return cote_totale.quantize(Decimal('0.01'))
    
    def calculer_gain_potentiel(self):
        return (self.mise * self.cote_totale).quantize(Decimal('0.01'))
    
    def mettre_a_jour_statut(self):
        paris_actifs = self.paris.filter(actif=True)
        
        if not paris_actifs.exists():
            self.statut = 'ANNULE'
            return
        
        if any(pari.resultat == 'NaN' for pari in paris_actifs):
            self.statut = 'EN_COURS'
            return
            
        if all(pari.selection == pari.resultat for pari in paris_actifs):
            self.statut = 'GAGNE'
        else:
            self.statut = 'PERDU'
    
    def clean(self):
        super().clean()
        # Vérifie que les paris simples n'ont qu'un seul pari
        if self.type_pari == 'SIMPLE' and self.paris.count() > 1:
            raise ValidationError("Un pari simple ne peut contenir qu'un seul pari")
    
    def save(self, *args, **kwargs):
        # Détermine automatiquement le type de pari
        if self.paris.count() <= 1:
            self.type_pari = 'SIMPLE'
        else:
            self.type_pari = 'COMBINE'
            
        self.cote_totale = self.calculer_cote_totale()
        self.gain_potentiel = self.calculer_gain_potentiel()
        self.mettre_a_jour_statut()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Groupe de paris"
        verbose_name_plural = "Groupes de paris"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.get_type_pari_display()} #{self.id} - {self.statut}"

class Pari(models.Model):
    """Modèle pour les paris individuels"""
    id = models.BigAutoField(primary_key=True)
    
    groupe = models.ForeignKey(
        GroupePari,
        on_delete=models.CASCADE,
        related_name="paris",
        verbose_name="Groupe de paris"
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
        
        # Vérifie que le pari respecte le type de son groupe
        if self.groupe.type_pari == 'SIMPLE' and self.groupe.paris.exclude(pk=self.pk).exists():
            raise ValidationError("Ce groupe est un pari simple et ne peut contenir qu'un seul pari")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        self.groupe.save()  # Met à jour le groupe après chaque modification du pari

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