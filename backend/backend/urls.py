from django.urls import path
from requests_app.views import ResponseCreateView, OfferCreateView, UserLoginViaRequestView
from requests_app import urls as requests_urls
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse
from django.urls import path, include
from requests_app.views import AdminLoginView
from django.conf import settings
from django.conf.urls.static import static
from requests_app.views import UserRequestsView, UserLoginViaRequestView
from requests_app.views import CustomTokenRefreshView
from django.views.generic import TemplateView
from django.urls import re_path
from django.views.generic import View
from django.http import HttpResponse
import os


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
    path("api/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path('api/admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('api/admin/token/refresh/', TokenRefreshView.as_view(), name='admin_token_refresh'),
    path("api/offers/", OfferCreateView.as_view(), name="offer-create"),
    path("api/users/login-via-request/", UserLoginViaRequestView.as_view(), name="user-login-via-request"),
    path("api/users/requests/", UserRequestsView.as_view(), name="user-requests"),
]

# Serve media during DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# Angular SPA catch-all (ali ne za API, static ili media)
class AngularAppView(View):
    def get(self, request, *args, **kwargs):
        index_path = os.path.join(settings.BASE_DIR, 'wwwroot', 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())


urlpatterns += [
    re_path(r'^(?!api/|static/|media/).*$', AngularAppView.as_view()),
]
