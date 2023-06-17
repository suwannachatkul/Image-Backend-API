import logging

from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .serializers import CookieTokenRefreshSerializer

logger = logging.getLogger(__name__)


class CookieTokenObtainPairView(TokenObtainPairView):

    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get('refresh'):
            cookie_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
            response.set_cookie('refresh_token', response.data['refresh'], max_age=cookie_max_age, httponly=True)
        return super().finalize_response(request, response, *args, **kwargs)


class CookieTokenRefreshView(TokenRefreshView):

    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get('refresh'):
            cookie_max_age = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
            response.set_cookie('refresh_token', response.data['refresh'], max_age=cookie_max_age, httponly=True)
            del response.data['refresh']
        return super().finalize_response(request, response, *args, **kwargs)

    serializer_class = CookieTokenRefreshSerializer

class CookieTokenDeleteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response()
        response.delete_cookie('refresh_token')
        response.data = {'message': 'Logout successful. Cookies deleted.'}
        return response