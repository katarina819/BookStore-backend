from django.contrib import admin
from django.utils.html import format_html
from .models import Offer, OfferImage

class OfferImageInline(admin.TabularInline):  # ili admin.StackedInline
    model = OfferImage
    extra = 3  # prikaži 3 prazna polja za upload
    fields = ['image', 'image_preview']  # polje za upload + preview
    readonly_fields = ['image_preview']  # preview samo za čitanje

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'city', 'price']
    inlines = [OfferImageInline]


@admin.register(OfferImage)
class OfferImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'offer', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 75px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"
