from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.conf import settings
from rest_framework.permissions import AllowAny


class TokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            # TODO implement expired token
            # if not created and token.expire_at < datetime.now():
            #     # if token has expired, delete it and create a new one
            #     token.delete()
            #     token = Token.objects.create(user=user)
            # token.expire_at = datetime.now() + settings.TOKEN_EXPIRE_TIME 
            # token.save()
            return Response({'token': f'Bearer {token.key}'})
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
