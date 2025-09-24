from rest_framework import serializers
from .models import Requests, Response, RelocationRequest, TimeRequest, AdminUser, Offer, OfferImage
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import AdminUser
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from datetime import timedelta
import bcrypt


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class RequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Requests
        fields = "__all__"

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        instance = super().create(validated_data)
        instance.set_password(raw_password)  # hashiraj lozinku
        return instance

    def update(self, instance, validated_data):
        if "password" in validated_data:
            raw_password = validated_data.pop("password")
            instance.set_password(raw_password)
        return super().update(instance, validated_data)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "username", "email"]


class ResponseSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    admin = AdminUserSerializer(read_only=True)
    message_type = serializers.SerializerMethodField()  # virtualno polje

    class Meta:
        model = Response
        fields = ['id', 'request', 'admin', 'message', 'created_at', 'message_type']

    def get_message_type(self, obj):
        return 'admin' if obj.admin else 'user'


class RelocationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelocationRequest
        fields = [
            "id", "request", "city", "postcode", "stay_type", "accommodation_type",
            "for_whom", "others", "pet", "pet_type", "distance", "price_range",
            "req_parking", "req_garage", "req_balcony", "req_terrace",
            "req_shops", "req_center", "req_hospital", "message"
        ]


class TimeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeRequest
        fields = "__all__"

    def to_internal_value(self, data):
        if "accommodationDate" in data:
            data["accommodation_date"] = data.pop("accommodationDate")
        if "knowDuration" in data:
            value = data.pop("knowDuration")
            data["know_duration"] = True if value in ["Yes", "yes", True] else False
        return super().to_internal_value(data)



class OfferImageSerializer(serializers.ModelSerializer):
    full_image_url = serializers.SerializerMethodField()

    class Meta:
        model = OfferImage
        fields = ['offer', 'image_url', 'image', 'full_image_url']
        extra_kwargs = {
            'offer': {'required': True},
        }

    def get_full_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:  # Cloudinary ili lokalni ImageField
            if request:  # puni URL za frontend
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        elif obj.image_url:  # eksterni URL
            return obj.image_url
        return ''  # fallback


class OfferSerializer(serializers.ModelSerializer):
    images = OfferImageSerializer(many=True, read_only=True)
    request = serializers.PrimaryKeyRelatedField(
        queryset=Requests.objects.all(), write_only=True
    )

    class Meta:
        model = Offer
        fields = [
            'id', 'request', 'type', 'city', 'address',
            'price', 'description', 'images'
        ]


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            admin = AdminUser.objects.get(email=email)
        except AdminUser.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid credentials"})

        if not bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            raise serializers.ValidationError({"detail": "❌ Incorrect email or password"})

        refresh = RefreshToken.for_user(admin)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": admin.id,
                "email": admin.email,
                "username": admin.username,
                "is_admin": True
            }
        }



class RequestDetailSerializer(serializers.ModelSerializer):
    relocations = RelocationRequestSerializer(many=True, read_only=True)
    time_requests = TimeRequestSerializer(many=True, read_only=True)
    responses = ResponseSerializer(many=True, read_only=True)
    offers = OfferSerializer(many=True, read_only=True)

    class Meta:
        model = Requests
        fields = [
            'id', 'name', 'surname', 'email', 'contact', 'address', 'residence', 'postal',
            'alcohol', 'smoker', 'employed', 'criminal', 'status', 'created_at',
            'relocations',
            'time_requests',
            'responses',
            'offers',
        ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if 'request' in self.context:
            context['request'] = self.context['request']
        return context


class AdminRequestSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Requests
        fields = ['id', 'name', 'surname', 'email', 'status', 'responses']


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])


        data = {'access': str(refresh.access_token)}


        data['user'] = {
            "id": refresh.get("user_id"),
            "email": refresh.get("email"),
            "name": refresh.get("name"),
            "surname": refresh.get("surname"),
            "is_request_user": refresh.get("is_request_user", False),
            "is_admin": refresh.get("is_admin", False),
        }

        return data


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # custom claims
        token['username'] = user.username
        token['is_admin'] = True
        return token