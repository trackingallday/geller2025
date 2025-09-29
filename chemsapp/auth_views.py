from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q


class CustomAuthToken(ObtainAuthToken):
    """
    Custom authentication token view that accepts both username and email
    """

    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get('username')
        password = request.data.get('password')

        if not username_or_email or not password:
            return Response({
                'error': 'Both username/email and password are required'
            }, status=400)

        # First try to authenticate with username
        user = authenticate(request, username=username_or_email, password=password)

        # If that fails, try to find user by email and authenticate
        if user is None:
            try:
                # Find user by email
                email_user = User.objects.get(email=username_or_email)
                # Try to authenticate using the found user's username
                user = authenticate(request, username=email_user.username, password=password)
            except User.DoesNotExist:
                pass

        if user and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=401)