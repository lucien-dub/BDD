from django.contrib import admin
from django.urls import path, include
from listings import views
from django.conf.urls import include


from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView # type: ignore
from listings.views import RegisterView, CustomTokenObtainPairView

from listings.views import MatchsAPIView, CotesAPIView
from listings.views import UserViewSet, UsersPointsAPIView, UpdateCotesView

user = DefaultRouter()
user.register(r'users', UserViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('about-us/', views.about),
    path('update-cotes/', UpdateCotesView.as_view(), name='update-cotes'),

    path('api-auth/', include('rest_framework.urls')),
    path('api/matchs/', MatchsAPIView.as_view()),
    path('api/cotes/', CotesAPIView.as_view()),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/user/', include(user.urls)),
    path('api/points/', UsersPointsAPIView.as_view()),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
