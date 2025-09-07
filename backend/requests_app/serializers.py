from rest_framework import serializers
from .models import Requests, Response, RelocationRequest, TimeRequest, AdminUser, Offer, OfferImage

from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class RequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Requests
        fields = "__all__"

class ResponseSerializer(serializers.ModelSerializer):
    request = RequestSerializer(read_only=True)
    admin = UserSerializer(read_only=True)

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


