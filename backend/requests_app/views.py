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
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Offer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import RequestUser
from rest_framework.permissions import IsAuthenticated
from .authentication import RequestUserJWTAuthentication
from .authentication import OptionalJWTAuthentication
# -----------------------------
# Public endpoints (no auth)
# -----------------------------
class PublicRequestCreateView(generics.CreateAPIView):
    queryset = Requests.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]


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
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        offer_id = self.request.data.get("offer")
        offer = Offer.objects.get(id=offer_id)
        # Ako dolazi fajl, spremi ga; ako dolazi URL, spremi URL
        image_file = self.request.data.get("image")
        image_url = self.request.data.get("image_url")
        serializer.save(offer=offer, image=image_file, image_url=image_url)




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
            return Response({"error": "All fields are required"}, status=400)

        user_requests = Requests.objects.filter(email=email, name=name, surname=surname)
        if not user_requests.exists():
            return Response({"error": "No requests found"}, status=401)

        request_user_obj, created = RequestUser.objects.get_or_create(
            request=user_requests.first(),
            defaults={"email": email, "name": name, "surname": surname}
        )

        refresh = RefreshToken.for_user(request_user_obj)
        refresh["email"] = email
        refresh["name"] = name
        refresh["surname"] = surname
        refresh["is_request_user"] = True

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {"email": email, "name": name, "surname": surname}
        })


class UserRequestsView(APIView):
    """
    Dohvat svih requestova za trenutno prijavljenog korisnika.
    Vraća kompletne podatke: relocations, time_requests, responses, offers + puni URL za slike.
    """
    authentication_classes = [RequestUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        req_user = request.user

        # Prefetch povezanih podataka
        user_requests = Requests.objects.filter(
            email=req_user.email,
            name=req_user.name,
            surname=req_user.surname
        ).prefetch_related(
            'relocations',
            'time_requests',
            'responses__admin',
            'offers__images'
        )

        # Serializer automatski uključuje sve polja iz Offer i OfferImage
        serializer = RequestDetailSerializer(user_requests, many=True, context={'request': request})
        data = serializer.data

        # Dodaj user-friendly poruke statusa
        for item in data:
            if item['status'] == 'pending':
                item['message'] = "Vaš zahtjev još nije obrađen od strane admina."
            elif item['status'] == 'responded':
                item['message'] = "Admin je odgovorio, ali ponude još nisu dostupne."
            elif item['status'] == 'resolved':
                item['message'] = None  # ili možeš staviti npr. "Ponude su dostupne"
                # offer['images'] sada već imaju full_image_url iz OfferImageSerializer

        return Response(data)


class RequestDetailView(generics.RetrieveAPIView):
    queryset = Requests.objects.all().prefetch_related(
        'relocations', 'time_requests', 'responses', 'offers'
    )
    serializer_class = RequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication]


class OfferWithImagesCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # 1. prvo kreiramo Offer
        offer_data = {
            "request": request.data.get("request"),
            "type": request.data.get("type"),
            "city": request.data.get("city"),
            "address": request.data.get("address"),
            "price": request.data.get("price"),
            "description": request.data.get("description"),
        }

        offer_serializer = OfferSerializer(data=offer_data)
        if not offer_serializer.is_valid():
            return Response(offer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        offer = offer_serializer.save()

        # 2. Označi request kao riješen
        req = Requests.objects.get(id=offer_data["request"])
        req.status = "resolved"
        req.save()

        # 2. dodaj sve slike koje dolaze pod "images"
        images = request.FILES.getlist("images")  # <--- OVDE PRIMIŠ SVE FAJLOVE
        image_objs = []
        for img in images:
            image_serializer = OfferImageSerializer(data={"offer": offer.id, "image": img})
            if image_serializer.is_valid():
                image_obj = image_serializer.save()
                image_objs.append(image_obj)
            else:
                # ako neka slika faila, obriši offer da ne ostane polovično
                offer.delete()
                return Response(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 3. vrati offer zajedno sa svim slikama
        return Response({
            "offer": OfferSerializer(offer).data,
            "images": OfferImageSerializer(image_objs, many=True).data
        }, status=status.HTTP_201_CREATED)