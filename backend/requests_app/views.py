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
    RequestDetailSerializer,
    CustomTokenRefreshSerializer
)
from django.contrib.auth.hashers import check_password
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from .serializers import AdminLoginSerializer, AdminRequestSerializer
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Offer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import RequestUser
from rest_framework.permissions import IsAuthenticated
from .authentication import RequestUserJWTAuthentication
from .authentication import OptionalJWTAuthentication
from rest_framework.response import Response as DRFResponse
from rest_framework_simplejwt.views import TokenViewBase
from .utils import get_tokens_for_request_user


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
    queryset = Requests.objects.all().prefetch_related('responses')
    serializer_class = AdminRequestSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]


class ResponseCreateView(generics.CreateAPIView):
    serializer_class = ResponseSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        req_id = self.request.data.get("request_id")
        request_obj = Requests.objects.get(id=req_id)

        # Get AdminUser instance
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

    def perform_create(self, serializer):
        offer = serializer.save()
        # postavi status requesta na resolved
        request_obj = offer.request
        request_obj.status = "resolved"
        request_obj.save()



class OfferImageCreateView(generics.CreateAPIView):
    serializer_class = OfferImageSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        offer_id = self.request.data.get("offer")
        request_id = self.request.data.get("request")

        if not offer_id and not request_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"request": "Request ID is required when offer is not provided."})

        # If the offer already exists
        if offer_id:
            try:
                offer = Offer.objects.get(id=offer_id)
            except Offer.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"offer": "Offer with this ID does not exist."})
        else:
            # Kreiraj novi offer obavezno vezan uz request
            try:
                request_obj = Requests.objects.get(id=request_id)
            except Requests.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"request": "Request with this ID does not exist."})

            offer_data = {
                "request": request_obj.id,   # uvijek ID, ne instanca!
                "type": self.request.data.get("type", "Apartment"),
                "city": self.request.data.get("city", ""),
                "address": self.request.data.get("address", ""),
                "price": self.request.data.get("price", 0),
                "description": self.request.data.get("description", ""),
            }

            offer_serializer = OfferSerializer(data=offer_data)
            offer_serializer.is_valid(raise_exception=True)
            offer = offer_serializer.save()

            # Mark request as resolved
            request_obj.status = "resolved"
            request_obj.save()

        # Upload image
        images = self.request.FILES.getlist("images")

        image_objs = []
        for img in images:
            image_serializer = OfferImageSerializer(data={"offer": offer.id, "image": img})
            image_serializer.is_valid(raise_exception=True)
            image_obj = image_serializer.save()
            image_objs.append(image_obj)

        self.image_objs = image_objs
        self.offer_instance = offer

    def create(self, request, *args, **kwargs):
        self.perform_create(None)
        return Response({
            "offer": OfferSerializer(self.offer_instance, context={"request": request}).data,
            "images": OfferImageSerializer(self.image_objs, many=True, context={"request": request}).data
        }, status=status.HTTP_201_CREATED)

# -----------------------------
# Admin login via SimpleJWT
# -----------------------------
class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # add custom claims
        token['username'] = user.username
        token['is_admin'] = True
        return token

    def validate(self, attrs):
        email = attrs.get("username")
        password = attrs.get("password")

        try:
            user = AdminUser.objects.get(email=email)
        except AdminUser.DoesNotExist:
            raise Exception("Invalid credentials")

        if not check_password(password, user.password_hash):
            raise Exception("Invalid credentials")


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
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            request_obj = Requests.objects.get(email=email)
        except Requests.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, request_obj.password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


        class DummyUser:
            def __init__(self, request_obj):
                self.id = request_obj.id
                self.pk = request_obj.pk
                self.is_active = True
                self.is_authenticated = True

        dummy_user = DummyUser(request_obj)

        refresh = RefreshToken.for_user(dummy_user)
        refresh["email"] = request_obj.email
        refresh["name"] = request_obj.name
        refresh["surname"] = request_obj.surname
        refresh["is_request_user"] = True

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": request_obj.id,
                "email": request_obj.email,
                "name": request_obj.name,
                "surname": request_obj.surname
            }
        }, status=status.HTTP_200_OK)

class UserRequestsView(APIView):
    """
    Retrieve all requests for the currently logged in user.
    Returns complete data: relocations, time_requests, responses, offers + full URL for images.
    """
    authentication_classes = [RequestUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_request = request.user


        user_request_qs = Requests.objects.filter(id=user_request.id).prefetch_related(
            'relocations',
            'time_requests',
            'responses__admin',
            'offers__images'
        )

        serializer = RequestDetailSerializer(user_request_qs, many=True, context={'request': request})
        data = serializer.data


        for item in data:
            if item['status'] == 'pending':
                item['message'] = "Your request has not yet been processed by the admin."
            elif item['status'] == 'responded':
                item['message'] = "Admin has responded, but offers are not yet available."
            elif item['status'] == 'resolved':
                item['message'] = "Offers are available."

        return Response(data, status=200)

class RequestDetailView(generics.RetrieveAPIView):
    queryset = Requests.objects.all().prefetch_related(
        'relocations', 'time_requests', 'responses', 'offers'
    )
    serializer_class = RequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication]

class OfferWithImagesCreateView(APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        request_id = request.data.get("request")
        if not request_id:
            return Response({"error": "Request ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            req = Requests.objects.get(id=request_id)
        except Requests.DoesNotExist:
            return Response({"error": "Request with this ID does not exist"}, status=status.HTTP_404_NOT_FOUND)

        # --- 1. Create new offer ---
        offer_data = {
            "request": req.id,
            "type": request.data.get("type"),
            "city": request.data.get("city"),
            "address": request.data.get("address"),
            "price": request.data.get("price"),
            "description": request.data.get("description"),
        }
        offer_serializer = OfferSerializer(data=offer_data)
        offer_serializer.is_valid(raise_exception=True)
        offer = offer_serializer.save()

        # Mark the request as solved
        req.status = "resolved"
        req.save()

        # --- 2. Add image ---
        images = request.FILES.getlist("images")
        image_objs = []
        for img in images:
            image_serializer = OfferImageSerializer(data={"offer": offer.id, "image": img})
            image_serializer.is_valid(raise_exception=True)
            image_obj = image_serializer.save()
            image_objs.append(image_obj)

        # --- 3. Restore data ---
        return Response({
            "offer": OfferSerializer(offer, context={"request": request}).data,
            "images": OfferImageSerializer(image_objs, many=True, context={"request": request}).data
        }, status=status.HTTP_201_CREATED)

class UserPayOfferView(APIView):
    authentication_classes = [RequestUserJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        offer_id = request.data.get("offer_id")
        if not offer_id:
            return DRFResponse({"error": "Offer ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            offer = Offer.objects.get(id=offer_id)
            request_obj = offer.request
        except Offer.DoesNotExist:
            return DRFResponse({"error": "Offer not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a Response for the notification
        ResponseModel.objects.create(
            request=request_obj,
            admin=None,
            message="User has paid this offer!"

        )

        return DRFResponse({"success": "Payment recorded and admin notified"}, status=status.HTTP_201_CREATED)


class AdminRequestDetailView(generics.RetrieveDestroyAPIView):
    queryset = Requests.objects.all()
    serializer_class = AdminRequestSerializer
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [JWTAuthentication]


class CustomTokenRefreshView(TokenViewBase):
    serializer_class = CustomTokenRefreshSerializer