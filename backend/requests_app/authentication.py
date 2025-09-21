from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from .models import RequestUser
from .models import RequestUser, Requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import Requests, AdminUser

User = get_user_model()


# -----------------------------
# JWT za RequestUser
# -----------------------------
class RequestUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token missing user_id")

        try:
            return Requests.objects.get(id=user_id)
        except Requests.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token for request user")



# -----------------------------
# Optional JWT
# -----------------------------
class OptionalJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):
        # If you want OptionalJWT to process the JWT if it exists, you can:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                validated_token = JWTAuthentication().get_validated_token(token)
                user = JWTAuthentication().get_user(validated_token)
                return (user, validated_token)
            except Exception:
                return None  # ignores invalid JWT
        return None  # if JWT does not exist, it does not throw 401


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Dohvati korisnika iz tokena, podržava RequestUser, AdminUser i Django User.
        """
        if validated_token.get("is_request_user"):
            try:
                return Requests.objects.get(id=validated_token["user_id"])
            except Requests.DoesNotExist:
                raise InvalidToken("Request user not found")
        elif validated_token.get("is_admin"):
            try:
                return AdminUser.objects.get(id=validated_token["user_id"])
            except AdminUser.DoesNotExist:
                raise InvalidToken("Admin user not found")
        else:
            try:
                return User.objects.get(id=validated_token["user_id"])
            except User.DoesNotExist:
                raise InvalidToken("User not found")


