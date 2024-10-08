from django.shortcuts import render
from django.http import HttpResponse

from listings.models import Matchs
from serializers.serializers import MatchsSerializer

from rest_framework.views import APIView
from rest_framework.response import Response


def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class MatchsAPIView(APIView):
 
    def get(self, *args, **kwargs):
        matchs = Matchs.objects.all()
        serializer = MatchsSerializer(matchs, many=True)
        return Response(serializer.data)
    