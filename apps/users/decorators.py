from functools import wraps

from django.http import JsonResponse
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .models import User


def jwt_required(view_func):
    """Decorator that validates JWT Bearer token and sets request.user."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth.startswith('Bearer '):
            return JsonResponse({'detail': 'Autentifikatsiya talab etiladi.'}, status=401)
        token_str = auth[7:].strip()
        try:
            token = AccessToken(token_str)
            user_id = token['user_id']
            request.user = User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return JsonResponse({'detail': 'Token noto\'g\'ri yoki muddati o\'tgan.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
