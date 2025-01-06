from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User


from background.actualisation_bdd import Match
from serializers.serializers import MatchSerializer
from serializers.serializers import UserSerializer, UserPointsSerializer, PointTransactionSerializer
from listings.models import UserPoints, PointTransaction

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
from serializers.serializers import UserSerializer, CustomTokenObtainPairSerializer



def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class MatchsAPIView(APIView):
 
    def get(self, *args, **kwargs):
        match = Match.objects.all()
        serializer = MatchSerializer(match, many=True)
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