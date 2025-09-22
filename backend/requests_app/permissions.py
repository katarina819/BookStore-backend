from rest_framework.permissions import BasePermission

class IsAdminCustom(BasePermission):
    """
    Gives access only to users who have is_admin = True.
    """
    def has_permission(self, request, view):
        # Checks if the user is authenticated and has is_admin = True
        return bool(request.user and getattr(request.user, 'is_admin', False))
