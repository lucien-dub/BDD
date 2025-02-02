from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from datetime import datetime, date

from creation_bdd.creation_bdd import Match

from listings.models import UserPoints, PointTransaction, User, Cote, Pari
from rest_framework import serializers

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model


class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['id','sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2', 'heure', 'niveau']

class CoteSerializer(ModelSerializer):
 
    class Meta:
        model = Cote
        fields = ['match','cote1','cote2','coteN']


class PariSerializer(serializers.ModelSerializer):
    match_details = MatchSerializer(source='match', read_only=True)
    cote_selection = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Pari
        fields = ['id', 'match', 'match_details', 'selection', 'actif', 
                 'resultat', 'username', 'cote_selection','mise', 'cote']
        read_only_fields = ['id','match','resultat', 'username', 'cote_selection']

    def get_cote_selection(self, obj):
        try:
            cote = obj.match.cotes.first()
            if not cote:
                return None
            
            if obj.selection == '1':
                return cote.cote1
            elif obj.selection == '2':
                return cote.cote2
            elif obj.selection == 'N':
                return cote.coteN
        except Exception:
            return None

    def validate_match(self, match):
        # Vérification si le match est terminé (basé sur la date/heure et scores)
        now = timezone.now()
        match_datetime = datetime.combine(match.date, match.heure)
    
        if match_datetime <= now:
            raise serializers.ValidationError(
                "Impossible de parier sur un match qui a déjà commencé"
            )

        # Vérification de l'existence d'une cote
        if not match.cotes.exists():
            raise serializers.ValidationError(
                "Pas de cotes disponibles pour ce match"
            )

        return match

    def validate_selection(self, selection):
        if selection not in ['1', '2', 'N']:
            raise serializers.ValidationError(
                "La sélection doit être '1', '2' ou 'N'"
            )
        return selection

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            # Vérification du pari existant
            existing_bet = Pari.objects.filter(
                match=data['match'],
                user=request.user,
                actif=True
            ).exists()
            
            if existing_bet and self.instance is None:
                raise serializers.ValidationError(
                    "Vous avez déjà un pari actif sur ce match"
                )

        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)

class PariListSerializer(serializers.ModelSerializer):
    match_info = serializers.SerializerMethodField()
    cote_selection = serializers.SerializerMethodField()
    
    class Meta:
        model = Pari
        fields = ['id', 'selection', 'actif', 'resultat', 'match_info', 
                 'cote_selection']
        
    def get_match_info(self, obj):
        match = obj.match
        return {
            'sport': match.sport,
            'date': match.date,
            'heure': match.heure,
            'equipe1': match.equipe1,
            'equipe2': match.equipe2,
            'score1': match.score1,
            'score2': match.score2,
            'niveau': match.niveau,
            'poule': match.poule
        }
    
    def get_cote_selection(self, obj):
        cote = obj.match.cotes.first()
        if not cote:
            return None
            
        if obj.selection == '1':
            return cote.cote1
        elif obj.selection == '2':
            return cote.cote2
        elif obj.selection == 'N':
            return cote.coteN

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