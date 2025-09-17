from rest_framework.permissions import IsAuthenticated


class CanEditCartItemPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.cart.customer == request.user


class CanConfirmCartPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return True
        # return obj.user == request.user
