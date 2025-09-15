from django.urls import path
from .views import (
    PublicRequestCreateView, RequestsListView, RelocationRequestCreateView, TimeRequestCreateView,
    UserLoginViaRequestView, UserRequestsView, RequestDetailView, OfferImageCreateView, OfferCreateView, OfferWithImagesCreateView

)

urlpatterns = [
    path('', RequestsListView.as_view(), name='requests-list'),       # GET
    path('create/', PublicRequestCreateView.as_view(), name='public-request-create'),  # POST
    path('relocation/', RelocationRequestCreateView.as_view(), name='relocation-create'),
    path('time/', TimeRequestCreateView.as_view(), name='time-create'),
    path('users/login-via-request/', UserLoginViaRequestView.as_view(), name='user-login-via-request'),
    path('user/requests/', UserRequestsView.as_view(), name='user-requests'),
    path("<int:pk>/", RequestDetailView.as_view(), name="request-detail"),
    path("offer-images/", OfferImageCreateView.as_view(), name="offer-image-create"),
    path("offers/", OfferCreateView.as_view(), name="offer-create"),
    path("offers/with-images/", OfferWithImagesCreateView.as_view(), name="offer-with-images-create"),


]

