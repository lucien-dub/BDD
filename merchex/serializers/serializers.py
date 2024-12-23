from rest_framework.serializers import ModelSerializer
from listings.models import CustomUser
from creation_bdd.creation_bdd import Match
 
class MatchSerializer(ModelSerializer):
 
    class Meta:
        model = Match
        fields = ['sport', 'date', 'equipe1', 'equipe2', 'score1', 'score2']
        

class UserSerializer(ModelSerializer):
    
    class Meta:
        model = CustomUser
        fields =  ['id','username','email','points']