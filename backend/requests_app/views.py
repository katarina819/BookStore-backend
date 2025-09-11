from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Requests, Response as ResponseModel, RelocationRequest, TimeRequest, AdminUser
from .serializers import (
    RequestSerializer,
    RelocationRequestSerializer,
    TimeRequestSerializer,
    ResponseSerializer,
    OfferSerializer,
    OfferImageSerializer,
    RequestDetailSerializer
)
from django.contrib.auth.hashers import check_password
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from .serializers import AdminLoginSerializer
from rest_framework.exceptions import AuthenticationFailed
# -----------------------------
# Public endpoints (no auth)
# -----------------------------
class PublicRequestCreateView(generics.CreateAPIView):
    queryset = Requests.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [AllowAny]


class RelocationRequestCreateView(generics.CreateAPIView):
    queryset = RelocationRequest.objects.all()
    serializer_class = RelocationRequestSerializer
    permission_classes = [AllowAny]


class TimeRequestCreateView(generics.CreateAPIView):
    queryset = TimeRequest.objects.all()
    serializer_class = TimeRequestSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        req_id = self.request.data.get("request")
        try:
            request_obj = Requests.objects.get(id=req_id)
        except Requests.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"request": "Request with this ID does not exist."})
        serializer.save(request=request_obj)


# -----------------------------
# Admin endpoints
# -----------------------------
class RequestsListView(generics.ListAPIView):
    queryset = Requests.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]


class ResponseCreateView(generics.CreateAPIView):
    serializer_class = ResponseSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        req_id = self.request.data.get("request_id")
        request_obj = Requests.objects.get(id=req_id)

        # Dohvati AdminUser instancu
        user_id = getattr(self.request.user, 'id', None)  # ovo dolazi iz JWT
        try:
            admin_user = AdminUser.objects.get(id=user_id)
        except AdminUser.DoesNotExist:
            raise AuthenticationFailed("Invalid admin user")

        serializer.save(admin=admin_user, request=request_obj)

        request_obj.status = "responded"
        request_obj.save()


class OfferCreateView(generics.CreateAPIView):
    serializer_class = OfferSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]


class OfferImageCreateView(generics.CreateAPIView):
    serializer_class = OfferImageSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]



# -----------------------------
# Admin login via SimpleJWT
# -----------------------------
class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # dodaj custom claimove
        token['username'] = user.username
        token['is_admin'] = True
        return token

    def validate(self, attrs):
        email = attrs.get("username")  # SimpleJWT očekuje "username" field
        password = attrs.get("password")

        try:
            user = AdminUser.objects.get(email=email)
        except AdminUser.DoesNotExist:
            raise Exception("Invalid credentials")

        if not check_password(password, user.password_hash):
            raise Exception("Invalid credentials")

        # hack: SimpleJWT očekuje Django User objekt → kreiramo dummy user
        from django.contrib.auth.models import AnonymousUser
        dummy_user = AnonymousUser()
        dummy_user.id = user.id
        dummy_user.username = user.username
        dummy_user.is_staff = True
        dummy_user.is_superuser = True

        data = super().validate({
            "username": dummy_user.username,
            "password": password
        })
        data["user"] = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_admin": True
        }
        return data


class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminLoginSerializer

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer


# -----------------------------
# User endpoints (login via request)
# -----------------------------
class UserLoginViaRequestView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        name = request.data.get("name")
        surname = request.data.get("surname")

        if not email or not name or not surname:
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        user_requests = Requests.objects.filter(email=email, name=name, surname=surname)
        if not user_requests.exists():
            return Response({"error": "No requests found for this user"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generiraj JWT token (1h)
        payload = {
            "email": email,
            "name": name,
            "surname": surname,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return Response({
            "token": token,
            "user": {
                "email": email,
                "name": name,
                "surname": surname
            }
        })


class UserRequestsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_email = getattr(request.user, 'email', None)
        user_name = getattr(request.user, 'name', None)
        user_surname = getattr(request.user, 'surname', None)

        user_requests = Requests.objects.filter(email=user_email, name=user_name, surname=user_surname)
        data = [{"id": r.id, "status": getattr(r, "status", "pending"), "created_at": r.created_at} for r in user_requests]
        return Response(data)


class RequestDetailView(generics.RetrieveAPIView):
    queryset = Requests.objects.all().prefetch_related(
        'relocations', 'time_requests', 'responses', 'offers'
    )
    serializer_class = RequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication]


