from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.views import View


from background.actualisation_bdd import Match
from background.odds_calculator import calculer_cotes
from serializers.serializers import MatchSerializer, CoteSerializer
from serializers.serializers import UserSerializer, UserPointsSerializer, PointTransactionSerializer
from listings.models import UserPoints, PointTransaction, Cote, Pari

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
from serializers.serializers import UserSerializer, CustomTokenObtainPairSerializer, PariListSerializer, PariSerializer

import logging
from django.db.models import Q
from django.core.paginator import Paginator

def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class PariViewSet(viewsets.ModelViewSet):
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PariListSerializer
        return PariSerializer
    
    def get_queryset(self):
        return Pari.objects.filter(user=self.request.user)
    
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
                matches = matches.filter(
                    Q(sport__icontains=query) |
                    Q(equipe1__icontains=query) |
                    Q(equipe2__icontains=query) |
                    Q(niveau__icontains=query) |
                    Q(poule__icontains=query)
                ).order_by('-date', '-heure')

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