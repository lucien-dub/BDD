import jwt
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import logging

logger = logging.getLogger(__name__)

class AutoTokenRenewalMiddleware:
    """
    Middleware qui vérifie automatiquement l'expiration des tokens
    et les renouvelle si nécessaire lors de chaque requête
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Seuil de renouvellement : 7 jours avant expiration
        self.renewal_threshold = 7 * 24 * 60 * 60  # 7 jours en secondes

    def __call__(self, request):
        # Traiter la requête avant la vue
        self.process_request(request)
        
        # Traiter la requête
        response = self.get_response(request)
        
        # Traiter la réponse après la vue
        return self.process_response(request, response)

    def process_request(self, request):
        """Vérifie et renouvelle le token si nécessaire"""
        
        # Ignorer certaines URL qui n'ont pas besoin d'authentification
        skip_paths = ['/api/login/', '/api/register/', '/api/token/', '/admin/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
            
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header[7:]
        
        try:
            # Décoder le token sans vérifier la signature pour obtenir les informations
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'], options={"verify_signature": False})
            exp_timestamp = payload.get('exp')
            user_id = payload.get('user_id')
            
            if not exp_timestamp or not user_id:
                return None
                
            current_timestamp = timezone.now().timestamp()
            time_until_expiry = exp_timestamp - current_timestamp
            
            # Si le token expire dans moins de 7 jours, le marquer pour renouvellement
            if time_until_expiry < self.renewal_threshold:
                request.should_renew_token = True
                request.token_user_id = user_id
                logger.info(f"Token pour l'utilisateur {user_id} sera renouvelé - expire dans {time_until_expiry/3600:.1f}h")
            else:
                request.should_renew_token = False
                
        except jwt.DecodeError:
            logger.warning("Token JWT invalide détecté dans le middleware")
            request.should_renew_token = False
        except Exception as e:
            logger.error(f"Erreur dans AutoTokenRenewalMiddleware: {str(e)}")
            request.should_renew_token = False
            
        return None

    def process_response(self, request, response):
        """Ajoute le nouveau token dans les headers de réponse si nécessaire"""
        
        # Vérifier si le token doit être renouvelé
        if (hasattr(request, 'should_renew_token') and 
            request.should_renew_token and 
            hasattr(request, 'user') and 
            request.user.is_authenticated):
            
            try:
                # Créer un nouveau token pour l'utilisateur
                refresh = RefreshToken.for_user(request.user)
                new_access_token = str(refresh.access_token)
                
                # Ajouter le nouveau token dans les headers de réponse
                response['X-New-Access-Token'] = new_access_token
                response['X-Token-Renewed'] = 'true'
                
                logger.info(f"Nouveau token généré automatiquement pour l'utilisateur {request.user.id}")
                
            except Exception as e:
                logger.error(f"Erreur lors du renouvellement automatique du token: {str(e)}")
                
        return response