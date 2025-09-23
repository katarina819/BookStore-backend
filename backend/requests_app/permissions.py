from rest_framework.permissions import BasePermission
from .models import AdminUser, Requests


class IsAdminCustom(BasePermission):
    """
    Gives access only to users who have is_admin = True.
    """
    def has_permission(self, request, view):
        # Checks if the user is authenticated and has is_admin = True
        return bool(request.user and getattr(request.user, 'is_admin', False))




class IsRequestOwnerOrAdmin(BasePermission):
    """
    Dopušta pristup:
    - ako je user AdminUser
    - ili ako je user Requests i pristupa svom vlastitom objektu
    """
    def has_object_permission(self, request, view, obj):
        # ako je admin, uvijek može
        if isinstance(request.user, AdminUser):
            return True

        # ako je običan Requests user, može samo svoj objekt
        if isinstance(request.user, Requests):
            return obj.id == request.user.id

        return False