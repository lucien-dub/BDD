# listings/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import os

def determiner_resultat_match(match):
    """
    Détermine le résultat d'un match (1, N, ou 2) en fonction des scores
    """
    if match.score1 > match.score2:
        return '1'
    elif match.score1 < match.score2:
        return '2'
    else:
        return 'N'

class Ecole(models.Model):
    # Supprimer la ligne id = models.BigAutoField() car Django le crée automatiquement
    lieu = models.CharField(max_length=100)

    def __str__(self):
        return self.lieu

class Equipe(models.Model):
    # Supprimer la ligne id = models.BigAutoField() car Django le crée automatiquement
    academie = models.CharField(max_length=100)
    poule = models.CharField(max_length=100)  # Correction de Charfield à CharField
    sport = models.CharField(max_length=100)  # Correction de Charfield à CharField

    def __str__(self):
        return f"{self.academie} - {self.sport}"


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
    match_joue = models.BooleanField(default=False)
    forfait_1 = models.BooleanField(default=False)
    forfait_2 = models.BooleanField(default=False)
    lieu = models.CharField(max_length=200,null=True, blank=True)
    arbitre = models.CharField(max_length=200, null=True, blank=True)
    commentaires = models.CharField(max_length=200,null=True, blank=True)
    academie = models.CharField(max_length=200, blank=True, default='')

    @property
    def est_termine(self):
        now = timezone.now()
        match_datetime = datetime.combine(self.date, self.heure)
        return match_datetime.timestamp() <= now.timestamp() or (self.score1 != 0 or self.score2 != 0)
    
    def save(self, *args, **kwargs):
        # Si les scores ont changé, vérifier les paris associés
        if self.pk:  # Si ce n'est pas une nouvelle création
            old_match = Match.objects.get(pk=self.pk)
            if (old_match.score1 != self.score1 or
                old_match.score2 != self.score2):

                # Optimisation : utiliser select_related pour éviter les requêtes N+1
                paris_actifs = self.paris.filter(actif=True).select_related('bet')

                # Pour chaque pari, vérifier le statut du groupe
                for pari in paris_actifs:
                    if pari.bet:  # Si le pari appartient à un groupe
                        pari.bet.verifier_statut()

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'creation_bdd_match'
        unique_together = ('sport', 'date', 'heure', 'equipe1', 'equipe2')
        indexes = [
            models.Index(fields=['sport', 'date']),
            models.Index(fields=['academie', 'date']),
            models.Index(fields=['date', 'heure']),
            models.Index(fields=['sport', 'niveau']),
        ]

    def __str__(self):
        return f"{self.equipe1} vs {self.equipe2} - {self.date}"
    
class Cote(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="cotes")
    coteN = models.DecimalField(max_digits=5, decimal_places=2, default=1.10)
    cote1 = models.DecimalField(max_digits=5, decimal_places=2, default=1.10)
    cote2 = models.DecimalField(max_digits=5, decimal_places=2, default=1.10)

    def __str__(self):
        return f"Cote pour {self.match},équipe1: {self.cote1}, équipe2: {self.cote2}, match nul :{self.coteN}"

class Bet(models.Model):
    id = models.BigAutoField(primary_key=True)
    mise = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    cote_totale = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    annule = models.BooleanField(default=False)

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
        indexes = [
            models.Index(fields=['user', 'actif']),
            models.Index(fields=['user', '-date_creation']),
            models.Index(fields=['actif', '-date_creation']),
        ]

    def verifier_statut(self):
        """
        Vérifie le statut de tous les paris du groupe et attribue les points si tous sont gagnants
        """
        tous_paris_gagnes = True
        paris_verifies = False  # Pour suivre si au moins un pari a été vérifié
        match_annule = False   # Pour suivre si un match est annulé

        # Optimisation : utiliser select_related pour éviter les requêtes N+1
        for pari in self.paris.select_related('match').all():
            match = pari.match
            
            # Vérifier si le match est terminé
            if match.est_termine:
                paris_verifies = True
                
                # Vérifier si le match est annulé (score NaN)
                if match.score1 == 'NaN' or match.score2 == 'NaN':
                    match_annule = True
                    break  # Sortir de la boucle car le bet sera annulé
                
                # Gérer les cas de forfait
                if match.forfait_1 and pari.selection == '1':
                    pari.resultat = 'F1'
                    pari.save()
                    continue
                    
                if match.forfait_2 and pari.selection == '2':
                    pari.resultat = 'F2'
                    pari.save()
                    continue
                
                resultat_match = determiner_resultat_match(match)
                
                # Si la sélection ne correspond pas au résultat
                if pari.selection != resultat_match:
                    tous_paris_gagnes = False
                    self.actif = False
                    self.save()
                    
                    # Mettre à jour le résultat du pari
                    pari.resultat = resultat_match
                    pari.actif = False
                    pari.save()
                    return False
                
                # Si le pari est gagnant, mettre à jour son résultat
                pari.resultat = resultat_match
                pari.save()

        # Si un match est annulé, rembourser la mise
        if match_annule:
            self.annule = True
            # Récupérer les points de l'utilisateur
            user_points = UserPoints.get_or_create_points(self.user)
            
            # Créer une transaction pour tracer le remboursement
            PointTransaction.objects.create(
                user=self.user,
                points=self.mise,  # Remboursement de la mise initiale
                transaction_type=PointTransaction.EARN,
                reason=f"Remboursement du pari #{self.id} - Match annulé"
            )
            
            # Rendre les points à l'utilisateur
            user_points.total_points += self.mise
            user_points.save()
            
            # Désactiver le pari
            self.actif = False
            self.save()
            
            # Marquer tous les paris comme annulés
            self.paris.all().update(actif=False, resultat='NaN')
            
            return False

        # Si tous les paris sont gagnants et au moins un pari a été vérifié
        if tous_paris_gagnes and paris_verifies:
            # Calculer les gains avec Decimal pour éviter les erreurs d'arrondi
            gains = int(Decimal(str(self.mise)) * Decimal(str(self.cote_totale)))

            # Récupérer ou créer les points de l'utilisateur
            user_points = UserPoints.get_or_create_points(self.user)
            
            # Créer une transaction pour tracer les points gagnés
            PointTransaction.objects.create(
                user=self.user,
                points=gains,
                transaction_type=PointTransaction.EARN,
                reason=f"Gains du pari combiné #{self.id}"
            )
            
            # Mettre à jour les points de l'utilisateur
            user_points.total_points += gains
            user_points.save()
            
            # Désactiver le pari car il est terminé et gagné
            self.actif = False
            self.save()
            
            # Désactiver tous les paris individuels
            self.paris.all().update(actif=False)
            
            return True
            
        return self.actif

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
        ('2', 'Victoire Équipe 2'),
        ('F1', 'Forfait Équipe 1'),
        ('F2', 'Forfait Équipe 2')
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
        indexes = [
            models.Index(fields=['match', 'actif']),
            models.Index(fields=['bet', 'actif']),
            models.Index(fields=['actif', 'resultat']),
        ]

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

class UserLoginTracker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='login_tracker')
    daily_login_count = models.IntegerField(default=0)
    total_login_count = models.IntegerField(default=0)  # ← Ajouter ce champ si manquant
    last_reset = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def increment_login_count(self):
        """Incrémente les compteurs et ajoute des points pour la première connexion quotidienne"""
        today = timezone.now().date()
        
        # Vérifier si c'est un nouveau jour
        if self.last_reset != today:
            self.last_reset = today
            self.daily_login_count = 0
        
        # Si c'est la première connexion du jour, ajouter des points
        if self.daily_login_count == 0:
            from .models import UserPoints, PointTransaction
            
            # Récupérer ou créer UserPoints
            user_points = UserPoints.get_or_create_points(self.user)
            
            # Ajouter 10 points
            user_points.total_points += 10
            user_points.save()
            
            # Créer une transaction
            PointTransaction.objects.create(
                user=self.user,
                points=10,
                transaction_type=PointTransaction.EARN,
                reason="Première connexion de la journée"
            )
        
        # Incrémenter les compteurs
        self.daily_login_count += 1
        self.total_login_count += 1  # ← Utiliser ce champ
        self.save()

    def __str__(self):
        return f"Login tracking for {self.user.username}"

@receiver(post_save, sender=User)
def create_user_login_tracker(sender, instance, created, **kwargs):
    """Crée automatiquement un UserLoginTracker pour chaque nouvel utilisateur"""
    if created:
        UserLoginTracker.objects.create(user=instance)

def user_directory_path(instance, filename):
    # Les fichiers seront uploadés dans MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'

class photo_profil(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo de profil de {self.user.username}"
    
    @property
    def photo_url(self):
        if self.photo:
            return f"{settings.MEDIA_URL}{self.photo}"
        return None
    

class Press(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE, verbose_name="Match associé")
    titre = models.CharField(max_length=200, verbose_name="Titre")
    texte = models.TextField(verbose_name="Description du match")
    sport = models.CharField(max_length=100, verbose_name="Sport")
    photo = models.ImageField(upload_to='press_photos/', blank=True, null=True, verbose_name="Photo du match")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    url_externe = models.URLField(blank=True, null=True, verbose_name="URL externe")
    
    class Meta:
        verbose_name = "Article de presse"
        verbose_name_plural = "Articles de presse"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Article: {self.titre} - Match: {self.match}"
    
class Academie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    academie = models.CharField(max_length=100, default='')


class Verification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    email_verified = models.BooleanField(default=False)
    accept_terms = models.BooleanField(default=False)

    # Add these to fix the clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='verification_user_set',
        blank=True,
        verbose_name=_('groups'),
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='verification_user_set',
        blank=True,
        verbose_name=_('user permissions'),
        help_text=_('Specific permissions for this user.'),
    )

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='verification_token')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=2)
            
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return timezone.now() <= self.expires_at
    
class Classement(models.Model):
    sport = models.CharField(max_length=100)
    niveau = models.CharField(max_length=50)
    poule = models.CharField(max_length=10)
    equipe = models.CharField(max_length=100)
    place = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    joues = models.IntegerField(default=0)  # J
    penalites = models.IntegerField(default=0)  # Pen
    gagnes = models.IntegerField(default=0)  # G
    nuls = models.IntegerField(default=0)  # N
    perdus = models.IntegerField(default=0)  # P
    gagnes_forfait = models.IntegerField(default=0)  # GF
    perdus_forfait = models.IntegerField(default=0)  # PF
    gagnes_tv = models.IntegerField(default=0)  # G TV
    perdus_tv = models.IntegerField(default=0)  # P TV
    buts_avantage = models.IntegerField(default=0)  # Ba
    buts_desavantage = models.IntegerField(default=0)  # Bd
    pour = models.IntegerField(default=0)
    contre = models.IntegerField(default=0)
    difference = models.IntegerField(default=0)  # Diff.
    academie = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['sport', 'niveau', 'poule', 'equipe', 'academie']
        ordering = ['sport', 'niveau', 'poule', 'place']

    def __str__(self):
        return f"{self.equipe} - {self.sport} {self.niveau} - Position {self.place}"

