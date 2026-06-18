from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsDoadorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.doador == request.user


class IsSolicitanteOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.solicitante == request.user


class IsDoadorDoPet(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.animal.doador == request.user
