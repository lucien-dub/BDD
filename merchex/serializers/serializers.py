from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from creation_bdd.creation_bdd import Match
from listings.models import User
from listings.models import UserPoint
 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2', 'heure']


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'prenom', 'nom', 'age', 'email', 'created_at', 'updated_at']


class UserPointSerializer(ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserPoint
        fields = ['id', 'username', 'points', 'last_updated']
