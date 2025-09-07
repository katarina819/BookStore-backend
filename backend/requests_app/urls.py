from django.urls import path
from .views import PublicRequestCreateView, RelocationRequestCreateView, TimeRequestCreateView

urlpatterns = [
    path('', PublicRequestCreateView.as_view(), name='public-request-create'),
    path('relocation/', RelocationRequestCreateView.as_view(), name='relocation-create'),
    path('time/', TimeRequestCreateView.as_view(), name='time-create'),
]
