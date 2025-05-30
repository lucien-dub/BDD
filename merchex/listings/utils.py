# listings/utils.py
# fichier contenant des fonctions transverses à l'application

from django.db.models import Q, Count, Sum, Avg, Case, When, IntegerField
from listings.models import Bet, Pari, UserPoints, PointTransaction
from decimal import Decimal
from django.conf import settings
from .models import EmailVerificationToken
from django.template.loader import render_to_string
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

def calculate_bet_statistics(user):
    """Calcule les statistiques de paris pour un utilisateur donné"""
    
    # Récupérer tous les paris de l'utilisateur
    user_bets = Bet.objects.filter(user=user).prefetch_related('paris', 'paris__match')
    
    if not user_bets.exists():
        return {
            'matchesPlayed': 0,
            'victories': 0,
            'defeats': 0,
            'winRate': '0%',
            'currentStreak': 0,
            'bestScore': 0,
            'totalBetsMade': 0,
            'matchesBetOn': 0,
            'betsWon': 0,
            'betsLost': 0,
            'betWinRate': '0%',
            'totalEarnings': 0,
            'activeBets': 0,
            'totalPointsSpent': 0,
            'averageBetAmount': 0,
            'biggestWin': 0
        }
    
    # Initialisation des variables
    total_bets = user_bets.count()
    active_bets = user_bets.filter(actif=True).count()
    completed_bets = user_bets.filter(actif=False)
    
    # Calculer les paris gagnés et perdus
    bets_won = 0
    bets_lost = 0
    total_earnings = 0
    biggest_win = 0
    current_streak = 0
    temp_streak = 0
    unique_matches = set()
    
    # Récupérer les paris triés par date pour calculer la série
    sorted_bets = completed_bets.order_by('-date_creation')
    
    for bet in sorted_bets:
        # Ajouter les matchs uniques
        for pari in bet.paris.all():
            if pari.match:
                unique_matches.add(pari.match.id)
        
        # Vérifier si le pari est gagnant
        all_paris_won = True
        all_paris_resolved = True
        
        for pari in bet.paris.all():
            if not pari.resultat or pari.resultat == "en_cours":
                all_paris_resolved = False
                break
            if pari.resultat == "perdu":
                all_paris_won = False
        
        if all_paris_resolved:
            if all_paris_won:
                bets_won += 1
                # Calculer les gains réels
                gain = float(bet.mise) * float(bet.cote_totale) if bet.mise and bet.cote_totale else 0
                total_earnings += gain
                if gain > biggest_win:
                    biggest_win = gain
                
                # Calculer la série actuelle (seulement pour les paris les plus récents)
                if current_streak == temp_streak:  # Si on est toujours dans la série actuelle
                    current_streak += 1
                temp_streak += 1
            else:
                bets_lost += 1
                current_streak = 0  # Reset de la série
                temp_streak += 1
    
    # Calculer les statistiques des points
    user_points = UserPoints.objects.filter(user=user).first()
    total_points_spent = PointTransaction.objects.filter(
        user=user, 
        transaction_type=PointTransaction.SPEND
    ).aggregate(Sum('points'))['points__sum'] or 0
    
    # Calculs finaux
    completed_bets_count = bets_won + bets_lost
    win_rate = (bets_won / completed_bets_count * 100) if completed_bets_count > 0 else 0
    average_bet = float(user_bets.aggregate(Avg('mise'))['mise__avg'] or 0)
    
    return {
        'matchesPlayed': len(unique_matches),
        'victories': bets_won,
        'defeats': bets_lost,
        'winRate': f"{win_rate:.1f}%",
        'currentStreak': current_streak,
        'bestScore': int(biggest_win),
        'totalBetsMade': total_bets,
        'matchesBetOn': len(unique_matches),
        'betsWon': bets_won,
        'betsLost': bets_lost,
        'betWinRate': f"{win_rate:.1f}%",
        'totalEarnings': f"{total_earnings:.2f}",
        'activeBets': active_bets,
        'totalPointsSpent': float(total_points_spent),
        'averageBetAmount': f"{average_bet:.2f}",
        'biggestWin': f"{biggest_win:.2f}",
        'currentPoints': float(user_points.total_points) if user_points else 0
    }

def send_verification_email(user):
    """Crée un token de vérification et envoie l'email"""
    try:
        # Supprimer les anciens tokens pour cet utilisateur
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Créer un nouveau token
        verification_token = EmailVerificationToken.objects.create(user=user)
        
        # Construire l'URL de vérification
        verification_url = f"{settings.FRONTEND_URL}api/verify-email/{verification_token.token}/"
        
        # Préparer le contexte pour le template
        context = {
            'user': user,
            'verification_url': verification_url,
        }
        
        # Rendre le template HTML
        html_message = render_to_string('email_verification.html', context)
        
        # Envoyer l'email
        send_mail(
            subject='Vérification de votre adresse email',
            message='',  # Message texte vide car on utilise HTML
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email de vérification envoyé avec succès à {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de vérification : {str(e)}")
        raise e
  