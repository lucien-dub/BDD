from rest_framework.serializers import ModelSerializer
 
from listings.models import Matchs
 
class MatchsSerializer(ModelSerializer):
 
    class Meta:
        model = Matchs
        fields = ['date', 'equipe1', 'equipe2', 'passe']
        