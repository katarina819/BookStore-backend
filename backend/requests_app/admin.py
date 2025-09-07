from django.contrib import admin
from .models import (
    AdminUser, Requests, RelocationRequest, TimeRequest,
    Offer, OfferImage
)

admin.site.register(AdminUser)
admin.site.register(Requests)
admin.site.register(RelocationRequest)
admin.site.register(TimeRequest)
admin.site.register(Offer)
admin.site.register(OfferImage)
