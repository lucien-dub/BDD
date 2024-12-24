from rest_framework.serializers import ModelSerializer
from creation_bdd.creation_bdd import Match

class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = '__all__'