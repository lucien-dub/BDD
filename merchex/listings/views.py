from django.shortcuts import render
from django.http import HttpResponse

from background.actualisation_bdd import Match
from serializers.serializers import MatchSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from models import CustomUser

def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class MatchsAPIView(APIView):
 
    def get(self, *args, **kwargs):
        match = Match.objects.all()
        serializer = MatchSerializer(match, many=True)
        return Response(serializer.data)
    

class UserPointsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({'username': user.username, 'points': user.points})