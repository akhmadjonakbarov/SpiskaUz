from rest_framework.permissions import IsAuthenticated


class CanEditCartItemPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        # return obj.cart.user == request.user
        return True


class CanConfirmCartPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return True
        # return obj.user == request.user
