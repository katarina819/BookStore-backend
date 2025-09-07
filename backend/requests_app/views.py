from rest_framework import generics, permissions
from .models import Requests, Response, RelocationRequest, TimeRequest
from .serializers import RequestSerializer, RelocationRequestSerializer, TimeRequestSerializer
from rest_framework.permissions import AllowAny
from .serializers import ResponseSerializer

class PublicRequestCreateView(generics.CreateAPIView):
    queryset = Requests.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [AllowAny]


class ResponseCreateView(generics.CreateAPIView):
    serializer_class = ResponseSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        req_id = self.request.data.get("request_id")
        request_obj = Requests.objects.get(id=req_id)
        serializer.save(admin=self.request.user, request=request_obj)
        request_obj.status = "responded"
        request_obj.save()


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
