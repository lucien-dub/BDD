from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from creation_bdd.creation_bdd import Match
from listings.models import User
from rest_framework import serializers
from listings.models import UserPoints, PointTransaction
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2', 'heure']


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'prenom', 'nom', 'age', 'email', 'created_at', 'updated_at']


class UserPointsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserPoints
        fields = ['username', 'total_points', 'last_updated']

class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ['points', 'transaction_type', 'reason', 'timestamp']


User = get_user_model()

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
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data