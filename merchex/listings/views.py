from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.views import View
from django.db.models import Prefetch


from background.actualisation_bdd import Match
from background.odds_calculator import calculer_cotes
from serializers.serializers import MatchSerializer, CoteSerializer
from serializers.serializers import UserSerializer, UserPointsSerializer, PointTransactionSerializer
from serializers.serializers import PariCreateSerializer, BetCreateSerializer
from listings.models import UserPoints, PointTransaction, Cote, Pari, Bet

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed

from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from serializers.serializers import UserSerializer, CustomTokenObtainPairSerializer, PariListSerializer, PariSerializer, BetSerializer

import logging
from django.db.models import Q
from django.core.paginator import Paginator

import logging

def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class PariViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PariListSerializer
        return PariSerializer
    
    def get_queryset(self):
        return Pari.objects.all()
    
logger = logging.getLogger(__name__)

class BetViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        try:
            # Récupérer tous les paris de l'utilisateur avec les relations nécessaires
            queryset = Bet.objects.filter(user=request.user).prefetch_related(
                Prefetch(
                    'paris',
                    queryset=Pari.objects.select_related('match')
                )
            ).order_by('-date_creation')
            
            # Préparer les données de réponse
            bets_data = []
            for bet in queryset:
                paris_data = []
                for pari in bet.paris.all():
                    paris_data.append({
                        'id': pari.id,
                        'match': {
                            'equipe1': pari.match.equipe1,
                            'equipe2': pari.match.equipe2,
                            'score1': pari.match.score1,
                            'score2': pari.match.score2,
                            'date': pari.match.date,
                            'heure': pari.match.heure,
                            'sport': pari.match.sport,
                            'niveau': pari.match.niveau
                        },
                        'selection': pari.selection,
                        'cote': str(pari.cote),
                        'resultat': pari.resultat,
                        'actif': pari.actif
                    })
                
                bet_data = {
                    'id': bet.id,
                    'mise': bet.mise,
                    'cote_totale': bet.cote_totale,
                    'gains_potentiels': round(float(bet.mise) * float(bet.cote_totale), 2),
                    'date_creation': bet.date_creation,
                    'actif': bet.actif,
                    'paris': paris_data
                }
                bets_data.append(bet_data)
            
            return Response({'bets': bets_data}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des paris: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la récupération des paris', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateBetView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        try:
            logger.info(f"Données reçues: {request.data}")

            # Récupérer les points de l'utilisateur
            user_points = UserPoints.get_or_create_points(request.user)
            mise = float(request.data.get('mise', 0))
            
            # Vérifier si l'utilisateur a assez de points
            if user_points.total_points < mise:
                return Response({
                    'error': 'Points insuffisants',
                    'details': f'Vous avez {user_points.total_points} points, mais la mise requiert {mise} points'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = BetCreateSerializer(data=request.data)

            serializer = BetCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                logger.error(f"Erreurs de validation: {serializer.errors}")
                return Response({
                    'error': 'Données invalides',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
              # Créer le pari et déduire les points dans la même transaction
            with transaction.atomic():
                # Créer le pari
                bet = serializer.save(user=request.user)
                
                # Déduire les points
                user_points.total_points -= mise
                user_points.save()
                
                # Enregistrer la transaction de points
                PointTransaction.objects.create(
                    user=request.user,
                    points=mise,
                    transaction_type=PointTransaction.SPEND,
                    reason=f"Mise placée sur le pari #{bet.id}"
                )
            
            return Response({
                'message': 'Pari créé avec succès',
                'bet_id': bet.id,
                'paris_ids': bet.paris_ids,
                'paris_cotes': bet.paris_cotes
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du pari: {str(e)}")
            return Response({
                'error': 'Erreur lors de la création du pari',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
class MatchsAPIView(APIView):
 
    def get(self, *args, **kwargs):
        match = Match.objects.all()
        serializer = MatchSerializer(match, many=True)
        return Response(serializer.data)

class CotesAPIView(APIView):

    def get(self, *args, **kwargs):
        cote = Cote.objects.all()
        serializer = CoteSerializer(cote, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class UsersPointsAPIView(APIView):

    def get(self, *args, **kwargs):
        users_points = UserPoints.objects.all()  # Récupère tous les UserPoints
        return JsonResponse([
            {'username': up.user.username, 'total_points': up.total_points} 
            for up in users_points
        ], safe=False)

logger = logging.getLogger(__name__)

class UpdateCotesView(View):
    def get(self, request):
        today = timezone.now().date()
        matches = Match.objects.filter(date__gte=today)
        results = []
        success_count = 0
        error_count = 0
        
        for match in matches:
            try:
                cote1, coteN, cote2 = calculer_cotes(match.id)
                results.append({
                    'match_id': match.id,
                    'status': 'success',
                    'equipe1': match.equipe1,
                    'equipe2': match.equipe2,
                    'date': match.date.strftime('%Y-%m-%d'),
                    'sport': match.sport,
                    'cotes': {
                        'cote1': cote1,
                        'coteN': coteN,
                        'cote2': cote2
                    }
                })
                success_count += 1
            except Exception as e:
                error_message = str(e)
                logger.error(f"Erreur lors du calcul des cotes pour le match {match.id}: {error_message}")
                results.append({
                    'match_id': match.id,
                    'status': 'error',
                    'equipe1': match.equipe1,
                    'equipe2': match.equipe2,
                    'date': match.date.strftime('%Y-%m-%d'),
                    'error': error_message
                })
                error_count += 1
        
        return JsonResponse({
            'results': results,
            'summary': {
                'total_matches': len(matches),
                'success_count': success_count,
                'error_count': error_count,
                'date_execution': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })

class VerifyBetsStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer tous les paris actifs de l'utilisateur
            bets = Bet.objects.filter(
                user=request.user,
                actif=True
            ).prefetch_related('paris', 'paris__match')
            
            updated_bets = []
            for bet in bets:
                initial_status = bet.actif
                bet.verifier_statut()
                
                if initial_status != bet.actif:
                    updated_bets.append({
                        'bet_id': bet.id,
                        'nouveau_statut': bet.actif
                    })
            
            return Response({
                'message': 'Vérification terminée',
                'paris_mis_a_jour': updated_bets
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des paris: {str(e)}")
            return Response({
                'error': 'Erreur lors de la vérification des paris',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Inscription réussie!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print("\n=== DEBUG LOGIN ATTEMPT ===")
        print("Données reçues:", request.data)
        print("Email reçu:", request.data.get('email'))
        print("Password reçu:", bool(request.data.get('password')))  # Pour la sécurité, on affiche juste si présent
        
        try:
            response = super().post(request, *args, **kwargs)
            print("Login réussi!")
            return response
        except Exception as e:
            print(f"Échec de login: {str(e)}")
            return Response(
                {'detail': 'Identifiants invalides'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class SearchMatchesAPIView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        try:
            print("=== DEBUG SEARCH ===")
            query = request.GET.get('query', '')
            print(f"Recherche reçue : {query}")
            matches = Match.objects.all()
           
            if query:
                # Séparer les termes de recherche
                search_terms = query.split()
                
                # Créer une requête Q initiale vide
                combined_query = Q()
                
                # Pour chaque terme, ajouter une condition AND
                for term in search_terms:
                    term_query = (
                        Q(sport__icontains=term) |
                        Q(equipe1__icontains=term) |
                        Q(equipe2__icontains=term) |
                        Q(niveau__icontains=term) |
                        Q(poule__icontains=term)
                    )
                    combined_query &= term_query
                
                matches = matches.filter(combined_query).order_by('-date', '-heure')
                
                print(f"Nombre de matches trouvés : {matches.count()}")
                serializer = MatchSerializer(matches, many=True)
                return Response({
                    'results': serializer.data,
                    'count': matches.count()
                })
            return Response({
                'results': [],
                'message': 'Aucun terme de recherche fourni'
            })
        except Exception as e:
            print(f"Erreur détaillée : {str(e)}")
            import traceback
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )