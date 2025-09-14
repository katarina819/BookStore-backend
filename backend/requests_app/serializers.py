from rest_framework import serializers
from .models import Requests, Response, RelocationRequest, TimeRequest, AdminUser, Offer, OfferImage
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import AdminUser
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class RequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Requests
        fields = "__all__"


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "username", "email"]



class ResponseSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    admin = AdminUserSerializer(read_only=True)

    class Meta:
        model = Response
        fields = "__all__"


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
        fields = ['id', 'image', 'image_url', 'full_image_url', 'created_at']

    def get_full_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            # puni URL za fajl sa servera
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        elif obj.image_url:
            # ako je unesena direktna URL adresa
            return obj.image_url
        return None


class OfferSerializer(serializers.ModelSerializer):
    images = OfferImageSerializer(many=True, read_only=True)

    class Meta:
        model = Offer
        fields = ['id', 'request', 'type', 'city', 'address', 'price', 'description', 'created_at', 'images']




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

        if not check_password(password, admin.password_hash):
            raise serializers.ValidationError({"detail": "Invalid credentials"})

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



