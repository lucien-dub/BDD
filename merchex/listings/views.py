from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from background.actualisation_bdd import Match
from serializers.serializers import MatchSerializer
from serializers.serializers import UserSerializer, UserPointSerializer
from listings.models import User, UserPoint

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import viewsets, permissions




def about(request):
    return HttpResponse('<h1>A propos</h1> <p>Nous adorons merch !</p>')


"""pour l'API"""
class MatchsAPIView(APIView):
 
    def get(self, *args, **kwargs):
        match = Match.objects.all()
        serializer = MatchSerializer(match, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserPointViewSet(viewsets.ModelViewSet):
    serializer_class = UserPointSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserPoint.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def my_points(self, request):
        user_points = get_object_or_404(UserPoint, user=request.user)
        serializer = self.get_serializer(user_points)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    def add_points(self, request):
        points_to_add = request.data.get('points', 0)
        user_points, created = UserPoint.objects.get_or_create(
            user=request.user,
            defaults={'points': 0}
        )
        user_points.points += points_to_add
        user_points.save()
        
        serializer = self.get_serializer(user_points)
        return Response(serializer.data)