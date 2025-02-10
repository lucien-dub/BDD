from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from listings import views
from listings.views import (
    RegisterView, 
    CustomTokenObtainPairView, 
    PariViewSet,
    MatchsAPIView, 
    CotesAPIView,
    UserViewSet, 
    UsersPointsAPIView, 
    UpdateCotesView,
    SearchMatchesAPIView,
    CreateBetView,
    BetViewSet,
    VerifyBetsStatusView,
)

# Configuration des routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'paris', PariViewSet, basename='pari')
router.register(r'bets', BetViewSet, basename='bets')

urlpatterns = [
    # Routes d'administration
    path('admin/', admin.site.urls),
    path('about-us/', views.about),
    
    # Routes d'authentification
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Routes API principales
    path('api/', include(router.urls)),  # Inclut toutes les routes du router
    
    # Routes pour les matchs et cotes
    path('api/matchs/', MatchsAPIView.as_view()),
    path('api/cotes/', CotesAPIView.as_view()),
    path('api/update-cotes/', UpdateCotesView.as_view(), name='update-cotes'),
    path('api/search-matches/', SearchMatchesAPIView.as_view(), name='search-matches'),
    
    # Routes pour les points utilisateurs
    path('api/points/', UsersPointsAPIView.as_view()),

    # Route pour placer un pari
    path('api/bets/create/', CreateBetView.as_view(), name='create-bet'),
    path('api/verify-bets/', VerifyBetsStatusView.as_view(), name='verify-bets'),
]