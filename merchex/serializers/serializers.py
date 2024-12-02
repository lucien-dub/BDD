from rest_framework.serializers import ModelSerializer
 
from merchex.creation_bdd.creation_bdd import Match
 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2']
        
