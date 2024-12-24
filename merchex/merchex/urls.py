"""
URL configuration for merchex project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from listings import views
from django.conf.urls import include
from  listings.views import UserPointViewSet

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView # type: ignore
from listings.views import MatchsAPIView
from listings.views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'user-points', UserPointViewSet, basename='user-points')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about-us/', views.about),
    path('api-auth/', include('rest_framework.urls')),
    path('api/matchs/', MatchsAPIView.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user', include(router.urls))
]
