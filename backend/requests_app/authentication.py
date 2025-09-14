# requests_app/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from .models import RequestUser

# -----------------------------
# 1️⃣ JWT za RequestUser (korisnika zahtjeva)
# -----------------------------
class RequestUserJWTAuthentication(JWTAuthentication):
    """
    Authentication class koja omogućava JWT login za RequestUser (korisnika zahtjeva)
    """
    def get_user(self, validated_token):
        try:
            email = validated_token.get("email")
            name = validated_token.get("name")
            surname = validated_token.get("surname")
            request_obj = RequestUser.objects.get(email=email, name=name, surname=surname)
            return request_obj
        except RequestUser.DoesNotExist:
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
