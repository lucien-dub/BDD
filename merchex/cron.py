from django.utils import timezone
from django.core.management import call_command
from listings.models import Match
from background.odds_calculator import calculer_cotes
from listings.models import UserLoginTracker
import logging

logger = logging.getLogger(__name__)

def update_all_cotes():
    """Met à jour toutes les cotes pour les matchs à venir"""
    try:
        today = timezone.now().date()
        matches = Match.objects.filter(date__gte=today)

        logger.info(f"Mise à jour des cotes pour {matches.count()} matchs")

        for match in matches:
            calculer_cotes(match.id)

        logger.info("Mise à jour des cotes terminée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des cotes: {str(e)}")

def update_matches_data():
    """Actualise les données des matchs depuis le site FFSU"""
    try:
        logger.info("Début de l'actualisation des données de matchs")
        call_command('update_matches')
        logger.info("Actualisation des matchs terminée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'actualisation des matchs: {str(e)}")

def update_classements_data():
    """Actualise les classements"""
    try:
        logger.info("Début de l'actualisation des classements")
        call_command('update_classements')
        logger.info("Actualisation des classements terminée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'actualisation des classements: {str(e)}")

def reset_login_counters():
    """Réinitialise tous les compteurs de connexion à minuit"""
    try:
        today = timezone.now().date()
        count = UserLoginTracker.objects.all().update(
            daily_login_count=0,
            last_reset=today
        )
        logger.info(f"Réinitialisation de {count} compteurs de connexion")
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation des compteurs: {str(e)}")