from django.urls import path

from .views import CookieTokenRefreshView, CookieTokenObtainPairView, CookieTokenDeleteView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', CookieTokenDeleteView.as_view(), name='token_delete'),
]