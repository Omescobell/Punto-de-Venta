from rest_framework import permissions

class IsAdminOrOwner(permissions.BasePermission):
    """
    Permiso personalizado que solo permite acceso a Administradores o Dueños.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['ADMIN', 'OWNER']