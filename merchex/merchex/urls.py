#merchex/urls.py
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
    PressViewSet,
    AcademieViewSet,
    VerifyEmailView, ResetPasswordView, LoginView, ForgotPasswordView,
)

from django.conf import settings
from django.conf.urls.static import static


# Configuration des routers
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'paris', PariViewSet, basename='pari')
router.register(r'bets', BetViewSet, basename='bets')
router.register(r'photos', views.PhotoProfilViewSet, basename='photo-profil')
router.register(r'press', PressViewSet)
router.register(r'academies', AcademieViewSet, basename='academie')

urlpatterns = [
    # Routes d'administration
    path('admin/', admin.site.urls),
    path('about-us/', views.about),
    
    # Routes d'authentification
    path('api-auth/', include('rest_framework.urls')),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/verify-email/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset-password'),

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)