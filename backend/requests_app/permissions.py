from rest_framework.permissions import BasePermission

class IsAdminCustom(BasePermission):
    """
    Daje pristup samo korisnicima koji imaju is_admin = True.
    """
    def has_permission(self, request, view):
        # Provjerava da li je korisnik autentificiran i da li ima is_admin = True
        return bool(request.user and getattr(request.user, 'is_admin', False))
