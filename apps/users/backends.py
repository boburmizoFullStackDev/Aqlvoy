from django.contrib.auth.backends import BaseBackend

from .models import User


class PhoneBackend(BaseBackend):
    def authenticate(self, request, phone=None, password=None, username=None, **kwargs):
        # Django admin passes the value as `username`; accept both
        phone = phone or username
        if not phone or not password:
            return None
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
