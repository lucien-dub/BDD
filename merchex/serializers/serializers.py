from rest_framework.serializers import ModelSerializer
 
from background.creation_bdd import Match
 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2']
        
