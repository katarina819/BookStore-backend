# requests_app/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from .models import RequestUser
from .models import RequestUser, Requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken


User = get_user_model()


# -----------------------------
# 1️⃣ JWT za RequestUser (korisnika zahtjeva)
# -----------------------------
class RequestUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")  # koristi ID iz tokena
        if not user_id:
            raise exceptions.AuthenticationFailed("Token missing user_id")

        try:
            return Requests.objects.get(id=user_id)
        except Requests.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token for request user")



# -----------------------------
# 2️⃣ Optional JWT za javne viewove
# -----------------------------
class OptionalJWTAuthentication(BaseAuthentication):
    """
    Ignorira JWT ako ga nema (za javne viewove).
    Ako JWT postoji, možeš ga parsirati (opcionalno)
    """
    def authenticate(self, request):
        # Ako želiš da OptionalJWT obradi JWT ako postoji, možeš:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                validated_token = JWTAuthentication().get_validated_token(token)
                user = JWTAuthentication().get_user(validated_token)
                return (user, validated_token)
            except Exception:
                return None  # ignorira nevažeći JWT
        return None  # ako JWT ne postoji, ne baca 401


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        if validated_token.get("is_request_user"):
            try:
                return Requests.objects.get(id=validated_token["user_id"])
            except Requests.DoesNotExist:
                raise InvalidToken("Request user not found")
        else:
            try:
                return User.objects.get(id=validated_token["user_id"])
            except User.DoesNotExist:
                raise InvalidToken("User not found")


