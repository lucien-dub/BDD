from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

from background.actualisation_bdd import Match
from serializers.serializers import MatchSerializer
from serializers.serializers import UserSerializer, UserPointsSerializer, PointTransactionSerializer
from listings.models import User
from listings.models import UserPoints, PointTransaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated


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


class UserPointsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPointsSerializer

    def get_queryset(self):
        return UserPoints.objects.filter(user=self.request.user)

    @action(detail=False, methods=['GET'])
    def my_points(self, request):
        points = UserPoints.get_or_create_points(request.user)
        serializer = self.get_serializer(points)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def add_points(self, request):
        points_to_add = request.data.get('points', 0)
        reason = request.data.get('reason', 'Points gagnés')

        if points_to_add <= 0:
            return Response(
                {'error': 'Le nombre de points doit être positif'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_points = UserPoints.get_or_create_points(request.user)
        user_points.total_points += points_to_add
        user_points.save()

        # Enregistrer la transaction
        PointTransaction.objects.create(
            user=request.user,
            points=points_to_add,
            transaction_type=PointTransaction.EARN,
            reason=reason
        )

        serializer = self.get_serializer(user_points)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def spend_points(self, request):
        points_to_spend = request.data.get('points', 0)
        reason = request.data.get('reason', 'Points dépensés')

        if points_to_spend <= 0:
            return Response(
                {'error': 'Le nombre de points doit être positif'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_points = UserPoints.get_or_create_points(request.user)

        if user_points.total_points < points_to_spend:
            return Response(
                {'error': 'Points insuffisants'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_points.total_points -= points_to_spend
        user_points.save()

        # Enregistrer la transaction
        PointTransaction.objects.create(
            user=request.user,
            points=points_to_spend,
            transaction_type=PointTransaction.SPEND,
            reason=reason
        )

        serializer = self.get_serializer(user_points)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def transaction_history(self, request):
        transactions = PointTransaction.objects.filter(
            user=request.user
        ).order_by('-timestamp')
        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data)