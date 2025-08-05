from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, email=None, phone_number=None, password=None, **kwargs):
        try:
            if email:
                user = User.objects.get(email=email)
            elif phone_number:
                user = User.objects.get(phone_number=phone_number)
            else:
                return None
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None