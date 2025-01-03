from django.contrib import admin
from django.urls import path, include
from listings import views
from django.conf.urls import include


from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView # type: ignore
from listings.views import RegisterView, CustomTokenObtainPairView

from listings.views import MatchsAPIView
from listings.views import UserViewSet, UserPointsViewSet

user = DefaultRouter()
user.register(r'users', UserViewSet)
router= DefaultRouter()
router.register(r'points', UserPointsViewSet, basename='points')

print(router.urls)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about-us/', views.about),

    path('api-auth/', include('rest_framework.urls')),
    path('api/matchs/', MatchsAPIView.as_view()),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/user/', include(user.urls)),
    path('api/points/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]
