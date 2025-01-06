from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from creation_bdd.creation_bdd import Match

from listings.models import UserPoints, PointTransaction, User
from rest_framework import serializers

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2', 'heure']


class UserPointsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserPoints
        fields = ['user', 'total_points', 'last_updated']

class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ['points', 'transaction_type', 'reason', 'timestamp']



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'username'

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username
        }
        return data
    

class VerifyUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        User = get_user_model()
        try:
            user = User.objects.get(email=email)  # Utilise l'email pour rechercher l'utilisateur
        except User.DoesNotExist:
            raise serializers.ValidationError('Utilisateur non trouvé.')

        if not user.check_password(password):
            raise serializers.ValidationError('Mot de passe incorrect.')

        return {'user': user}