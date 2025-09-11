from django.urls import path
from requests_app.views import ResponseCreateView
from requests_app import urls as requests_urls
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from django.urls import path, include
from requests_app.views import AdminLoginView
from django.conf import settings
from django.conf.urls.static import static

def root(request):
    return JsonResponse({
        "api_root": "/api/",
        "requests": "/api/requests/",
        "token": "/api/token/",
        "token_refresh": "/api/token/refresh/",
        "responses": "/api/responses/"
    })

urlpatterns = [
    path("", root, name="root"),
    path("api/requests/", include(requests_urls)),
    path("api/responses/", ResponseCreateView.as_view(), name="response-create"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('api/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/admin/token/refresh/', TokenRefreshView.as_view(), name='admin_token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)