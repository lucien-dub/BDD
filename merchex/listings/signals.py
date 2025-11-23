# listings/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Match, Bet, PointTransaction, Notification, Pari
from django.db.models import Q


@receiver(post_save, sender=Match)
def notifier_fin_match(sender, instance, created, **kwargs):
    """
    Notifie les utilisateurs quand un match où ils ont parié est terminé
    """
    # Ne notifier que si le match vient d'être marqué comme terminé
    if not created and instance.est_termine:
        # Récupérer tous les paris actifs sur ce match
        paris_sur_match = Pari.objects.filter(match=instance, actif=True).select_related('bet__user')

        # Créer un ensemble des utilisateurs à notifier (éviter les doublons)
        utilisateurs_notifies = set()

        for pari in paris_sur_match:
            if pari.bet and pari.bet.user and pari.bet.user.id not in utilisateurs_notifies:
                utilisateurs_notifies.add(pari.bet.user.id)

                # Créer la notification
                Notification.objects.create(
                    user=pari.bet.user,
                    type_notification=Notification.TYPE_MATCH_TERMINE,
                    titre=f"Match terminé: {instance.equipe1} vs {instance.equipe2}",
                    message=f"Le match {instance.equipe1} vs {instance.equipe2} est terminé. "
                           f"Score final: {instance.score1} - {instance.score2}. "
                           f"Vérifiez vos paris pour voir si vous avez gagné!",
                    match=instance
                )


@receiver(post_save, sender=Bet)
def notifier_resultat_pari(sender, instance, created, **kwargs):
    """
    Notifie l'utilisateur quand son pari est terminé (gagné, perdu ou remboursé)
    """
    # Ne notifier que si le pari vient d'être désactivé (terminé)
    if not created and not instance.actif and instance.user:
        # Vérifier si une notification existe déjà pour ce pari
        notification_existante = Notification.objects.filter(
            user=instance.user,
            bet=instance,
            type_notification__in=[
                Notification.TYPE_PARI_GAGNE,
                Notification.TYPE_PARI_PERDU,
                Notification.TYPE_PARI_REMBOURSE
            ]
        ).exists()

        if not notification_existante:
            # Déterminer le type de notification selon le résultat
            if instance.annule:
                # Pari remboursé (match annulé)
                Notification.objects.create(
                    user=instance.user,
                    type_notification=Notification.TYPE_PARI_REMBOURSE,
                    titre="Pari remboursé",
                    message=f"Votre pari #{instance.id} a été remboursé car un match a été annulé. "
                           f"Vous avez récupéré votre mise de {int(instance.mise)} points.",
                    bet=instance,
                    points=int(instance.mise)
                )
            else:
                # Vérifier si tous les paris sont gagnants
                tous_gagnants = True
                for pari in instance.paris.all():
                    if pari.resultat != pari.selection and pari.resultat not in ['F1', 'F2']:
                        tous_gagnants = False
                        break

                if tous_gagnants:
                    # Pari gagné
                    gains = int(instance.mise * instance.cote_totale)
                    Notification.objects.create(
                        user=instance.user,
                        type_notification=Notification.TYPE_PARI_GAGNE,
                        titre="🎉 Pari gagné!",
                        message=f"Félicitations! Votre pari #{instance.id} est gagnant! "
                               f"Vous avez gagné {gains} points avec une cote de {instance.cote_totale:.2f}. "
                               f"Les points ont été ajoutés à votre compte.",
                        bet=instance,
                        points=gains
                    )
                else:
                    # Pari perdu
                    Notification.objects.create(
                        user=instance.user,
                        type_notification=Notification.TYPE_PARI_PERDU,
                        titre="Pari perdu",
                        message=f"Votre pari #{instance.id} n'a pas été gagnant. "
                               f"Vous avez perdu {int(instance.mise)} points. "
                               f"Bonne chance pour vos prochains paris!",
                        bet=instance,
                        points=-int(instance.mise)
                    )


@receiver(post_save, sender=PointTransaction)
def notifier_gain_points(sender, instance, created, **kwargs):
    """
    Notifie l'utilisateur quand il gagne des points (hors paris)
    """
    # Ne notifier que pour les nouveaux gains de points
    # et uniquement si ce n'est pas lié à un pari (pour éviter les doublons)
    if created and instance.transaction_type == PointTransaction.EARN:
        # Vérifier si la raison n'est pas liée à un pari (pour éviter les doublons)
        if "pari" not in instance.reason.lower() and "bet" not in instance.reason.lower():
            Notification.objects.create(
                user=instance.user,
                type_notification=Notification.TYPE_POINTS_GAGNES,
                titre="Points gagnés!",
                message=f"Vous avez gagné {instance.points} points! "
                       f"Raison: {instance.reason}",
                points=instance.points
            )
