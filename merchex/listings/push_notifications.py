"""
Service de notifications push utilisant Firebase Cloud Messaging (FCM)
Gère l'envoi de notifications pour les paris terminés, bonus, etc.
"""
from pyfcm import FCMNotification
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service pour envoyer des notifications push via Firebase Cloud Messaging
    """

    def __init__(self):
        """
        Initialise le service FCM avec la clé API depuis les settings
        """
        self.fcm_api_key = getattr(settings, 'FCM_SERVER_KEY', None)
        if self.fcm_api_key:
            self.push_service = FCMNotification(api_key=self.fcm_api_key)
        else:
            self.push_service = None
            logger.warning("FCM_SERVER_KEY not configured in settings")

    def send_notification(self, user, title, message, notification_type, data=None):
        """
        Envoie une notification push à un utilisateur

        Args:
            user: L'utilisateur destinataire
            title: Titre de la notification
            message: Message de la notification
            notification_type: Type de notification (bet_won, bet_lost, etc.)
            data: Données additionnelles (dict)

        Returns:
            bool: True si au moins une notification a été envoyée avec succès
        """
        from .models import FCMDevice, PushNotification

        if not self.push_service:
            logger.error("FCM service not initialized")
            return False

        # Récupérer tous les appareils actifs de l'utilisateur
        devices = FCMDevice.objects.filter(user=user, active=True)

        if not devices.exists():
            logger.info(f"No active devices found for user {user.username}")
            return False

        # Préparer les données à envoyer
        notification_data = data or {}
        notification_data['notification_type'] = notification_type
        notification_data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

        # Extraire les tokens des appareils
        registration_ids = [device.registration_id for device in devices]

        success_count = 0
        error_message = None

        try:
            # Envoyer la notification à tous les appareils
            result = self.push_service.notify_multiple_devices(
                registration_ids=registration_ids,
                message_title=title,
                message_body=message,
                data_message=notification_data,
                sound='default',
                badge=1
            )

            # Analyser les résultats
            if result and result.get('success'):
                success_count = result.get('success', 0)
                logger.info(f"Successfully sent {success_count} notifications to {user.username}")

            # Gérer les tokens invalides
            if result and result.get('results'):
                for idx, res in enumerate(result['results']):
                    if res.get('error') == 'InvalidRegistration':
                        # Désactiver l'appareil avec un token invalide
                        device = devices[idx]
                        device.active = False
                        device.save()
                        logger.warning(f"Disabled invalid device token for {user.username}")

        except Exception as e:
            logger.error(f"Error sending notification to {user.username}: {str(e)}")
            error_message = str(e)

        # Enregistrer la notification dans l'historique
        notification_record = PushNotification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=notification_data,
            status='sent' if success_count > 0 else 'failed',
            sent_at=timezone.now() if success_count > 0 else None,
            error_message=error_message
        )

        return success_count > 0

    def send_bet_won_notification(self, bet):
        """
        Envoie une notification pour un pari gagné

        Args:
            bet: Instance du modèle Bet
        """
        gains = int(bet.mise * bet.cote_totale)
        title = "🎉 Pari gagné !"
        message = f"Félicitations ! Vous avez gagné {gains} points avec votre pari (cote {bet.cote_totale:.2f}x)"

        data = {
            'bet_id': bet.id,
            'gains': gains,
            'cote': float(bet.cote_totale),
            'mise': float(bet.mise)
        }

        return self.send_notification(
            user=bet.user,
            title=title,
            message=message,
            notification_type='bet_won',
            data=data
        )

    def send_bet_lost_notification(self, bet):
        """
        Envoie une notification pour un pari perdu

        Args:
            bet: Instance du modèle Bet
        """
        title = "❌ Pari perdu"
        message = f"Votre pari de {int(bet.mise)} points n'a pas été gagnant. Tentez votre chance à nouveau !"

        data = {
            'bet_id': bet.id,
            'mise': float(bet.mise),
            'cote': float(bet.cote_totale)
        }

        return self.send_notification(
            user=bet.user,
            title=title,
            message=message,
            notification_type='bet_lost',
            data=data
        )

    def send_bet_refunded_notification(self, bet):
        """
        Envoie une notification pour un pari remboursé

        Args:
            bet: Instance du modèle Bet
        """
        title = "💰 Pari remboursé"
        message = f"Votre pari de {int(bet.mise)} points a été remboursé suite à l'annulation d'un match."

        data = {
            'bet_id': bet.id,
            'mise': float(bet.mise)
        }

        return self.send_notification(
            user=bet.user,
            title=title,
            message=message,
            notification_type='bet_refunded',
            data=data
        )

    def send_daily_bonus_notification(self, user, points):
        """
        Envoie une notification pour le bonus quotidien

        Args:
            user: L'utilisateur
            points: Nombre de points gagnés
        """
        title = "🎁 Bonus quotidien"
        message = f"Vous avez reçu {points} points pour votre connexion du jour !"

        data = {
            'points': points
        }

        return self.send_notification(
            user=user,
            title=title,
            message=message,
            notification_type='daily_bonus',
            data=data
        )


# Instance globale du service
notification_service = PushNotificationService()
