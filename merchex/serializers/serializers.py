from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from datetime import datetime, date

from creation_bdd.creation_bdd import Match

from listings.models import UserPoints, PointTransaction, User, Cote, Pari, Bet, EmailVerificationToken
from listings.models import photo_profil, Press, Academie
from rest_framework import serializers

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

import logging

logger = logging.getLogger(__name__)

class PariCreateSerializer(serializers.ModelSerializer):
    match_id = serializers.IntegerField(write_only=True)
    odds = serializers.FloatField(source='cote')

    class Meta:
        model = Pari
        fields = ['match_id', 'selection', 'odds']

    def validate_selection(self, value):
        # Table de conversion
        selection_map = {
            'equipe1': '1',
            'equipe2': '2',
            'nul': 'N',
            # Garder aussi les valeurs déjà valides
            '1': '1',
            '2': '2',
            'n': 'N'
        }
        
        value = value.lower()
        if value not in selection_map:
            raise serializers.ValidationError(
                f"Selection invalide: {value}. "
                f"Valeurs acceptées: equipe1, equipe2, nul, 1, 2, N"
            )
            
        return selection_map[value]

class BetCreateSerializer(serializers.ModelSerializer):
    bets = PariCreateSerializer(many=True)
    total_odds = serializers.FloatField(write_only=True)
    potential_winnings = serializers.FloatField(write_only=True)
    
    class Meta:
        model = Bet
        fields = ['mise', 'total_odds', 'potential_winnings', 'bets']

    def validate(self, data):
        if not data.get('bets'):
            raise serializers.ValidationError("Au moins un pari est requis")
        
        if data['mise'] <= 0:
            raise serializers.ValidationError("La mise doit être supérieure à 0")
            
        if data['total_odds'] <= 0:
            raise serializers.ValidationError("La cote totale doit être supérieure à 0")
            
        calculated_winnings = data['mise'] * data['total_odds']
        if abs(calculated_winnings - data['potential_winnings']) > 0.01:
            raise serializers.ValidationError("Les gains potentiels ne correspondent pas au calcul mise * cote_totale")
            
        return data
    
    def create(self, validated_data):
        try:
            bets_data = validated_data.pop('bets')
            validated_data['cote_totale'] = validated_data.pop('total_odds')
            validated_data.pop('potential_winnings')
            
            paris_ids = []
            paris_cotes = {}
            
            bet = Bet.objects.create(**validated_data)
            
            for pari_data in bets_data:
                match_id = pari_data.pop('match_id')
                cote = pari_data['cote']
                
                pari = Pari.objects.create(
                    bet=bet,
                    match_id=match_id,
                    **pari_data
                )
                
                paris_ids.append(pari.id)
                paris_cotes[str(pari.id)] = float(cote)
            
            bet.paris_ids = paris_ids
            bet.paris_cotes = paris_cotes
            bet.save()
            
            return bet
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du pari: {str(e)}")
            raise serializers.ValidationError(f"Erreur lors de la création du pari: {str(e)}")


class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['id','sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2', 'heure', 'niveau', 'match_joue', 'forfait_1','forfait_2','academie']

class CoteSerializer(ModelSerializer):
 
    class Meta:
        model = Cote
        fields = ['match','cote1','cote2','coteN']


class PhotoProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = photo_profil
        fields = ['id', 'photo', 'date_upload']
        read_only_fields = ['user', 'date_upload']

class PariSerializer(serializers.ModelSerializer):
    match_details = MatchSerializer(source='match', read_only=True)
    cote_selection = serializers.SerializerMethodField()
    #groupe_id = serializers.PrimaryKeyRelatedField(source='groupe', read_only=True)
    
    class Meta:
        model = Pari
        fields = ['id', 'match', 'match_details', 'selection', 
                 'actif', 'resultat', 'cote_selection', 'cote']
        read_only_fields = ['id', 'resultat', 'cote_selection']

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
        now = timezone.now()
        match_datetime = datetime.combine(match.date, match.heure)
    
        if match_datetime <= now:
            raise serializers.ValidationError(
                "Impossible de parier sur un match qui a déjà commencé"
            )

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
    
class BetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ['id','actif', 'date_creation','cote_totale','mise']

    

class PariListSerializer(serializers.ModelSerializer):
    match_info = serializers.SerializerMethodField()
    cote_selection = serializers.SerializerMethodField()
    groupe_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Pari
        fields = ['id', 'groupe_details', 'selection', 'actif', 'resultat', 
                 'match_info', 'cote_selection', 'cote']
        
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

    def get_groupe_details(self, obj):
        groupe = obj.bet
        return {
            'id': groupe.id,
            'mise': groupe.mise,
            'cote_totale': groupe.cote_totale,
            'date_creation':groupe.date_creation,
        }

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
    username = serializers.CharField()  # <-- Modifié de email à username
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        User = get_user_model()
        
        try:
            # Si vous identifiez les utilisateurs par email dans votre base de données
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Utilisateur non trouvé.')
            
        if not user.check_password(password):
            raise serializers.ValidationError('Mot de passe incorrect.')
        return {'user': user}   


class PressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Press
        fields = ['id', 'match', 'titre', 'texte', 'sport', 'photo', 'date_creation', 
                 'date_modification', 'url_externe']
        read_only_fields = ['date_creation', 'date_modification']
    
    def validate_match(self, value):
        """
        Vérifier que le match existe
        """
        try:
            Match.objects.get(pk=value.id)
            return value
        except Match.DoesNotExist:
            raise serializers.ValidationError("Le match spécifié n'existe pas")
        

class AcademieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Academie
        fields = ['id', 'user', 'academie']
        read_only_fields = ['user']

class UserRegistrationSerializer(UserSerializer):
    confirm_password = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'accept_terms']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Les mots de passe ne correspondent pas'})
        
        if not data['accept_terms']:
            raise serializers.ValidationError({'accept_terms': 'Vous devez accepter les conditions générales d\'utilisation'})
        
        return data
    
    def create(self, validated_data):
        accept_terms = validated_data.pop('accept_terms', False)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        user.accept_terms = accept_terms
        user.email_verified = False
        user.save()
        return user