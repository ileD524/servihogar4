"""
Permisos personalizados para la API
"""
from rest_framework import permissions


class IsAdministrador(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios administradores
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'administrador'


class IsCliente(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios clientes
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'cliente'


class IsProfesional(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios profesionales
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'profesional'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso al dueño del objeto o a un administrador
    """
    def has_object_permission(self, request, view, obj):
        # Administradores tienen acceso completo
        if request.user.rol == 'administrador':
            return True
        
        # El dueño del objeto tiene acceso
        # Asume que el objeto tiene un campo 'usuario' o 'user'
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False
